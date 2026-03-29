"""Discogs authentication routes — OAuth 1.0a + personal token fallback."""

import secrets
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse, RedirectResponse

from ..discogs_client import (
    DISCOGS_CONSUMER_KEY,
    DISCOGS_TOKEN,
    fetch_identity,
    fetch_identity_oauth,
    fetch_user_profile,
    fetch_user_profile_oauth,
    get_access_token,
    get_request_token,
    oauth_configured,
)
from ..user_db import get_user_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# OAuth 1.0a temp token store (request_token -> request_secret)
# Short-lived: entries are consumed on callback within minutes
# ---------------------------------------------------------------------------
_oauth_temp: dict[str, str] = {}


def _generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def _ensure_session_token_column() -> None:
    """Add session_token column to users table if missing."""
    try:
        with get_user_db() as conn:
            cursor = conn.execute("PRAGMA table_info(users)")
            columns = {row["name"] for row in cursor.fetchall()}
            if columns and "session_token" not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN session_token TEXT")
                conn.commit()
    except Exception:
        pass  # Table may not exist yet — init_user_db() will create it


# Run migration on import (safe — handles missing table)
_ensure_session_token_column()


def _create_session(user_id: int, username: str, avatar_url: str) -> str:
    """Create a DB-backed session token for a user."""
    session_token = _generate_session_token()
    with get_user_db() as conn:
        conn.execute(
            "UPDATE users SET session_token = ? WHERE id = ?",
            (session_token, user_id),
        )
        conn.commit()
    return session_token


def _lookup_session(session_token: str) -> dict | None:
    """Look up a session token in the DB. Returns user dict or None."""
    if not session_token:
        return None
    with get_user_db() as conn:
        user = conn.execute(
            "SELECT id, discogs_username, avatar_url, synced_at "
            "FROM users WHERE session_token = ?",
            (session_token,),
        ).fetchone()
    if not user:
        return None
    return {
        "id": user["id"],
        "user_id": user["id"],  # alias for collection routes compatibility
        "discogs_username": user["discogs_username"],
        "avatar_url": user["avatar_url"],
        "synced_at": user["synced_at"],
    }


# ---------------------------------------------------------------------------
# Step 1: GET /api/auth/discogs/login
# ---------------------------------------------------------------------------


@router.get("/discogs/login")
def discogs_login(callback_url: str = Query("http://localhost:5173/auth/callback")):
    """Initiate Discogs authentication.

    OAuth 1.0a mode (DISCOGS_CONSUMER_KEY set): returns authorize_url.
    Fallback mode (personal token): authenticates directly, returns user info.
    """
    if oauth_configured():
        # Full OAuth 1.0a — get request token and return authorize URL
        try:
            request_token, request_secret, authorize_url = get_request_token(callback_url)
        except Exception as e:
            raise HTTPException(502, f"Failed to get Discogs request token: {e}")

        # Store request_secret for callback exchange
        _oauth_temp[request_token] = request_secret

        return {
            "mode": "oauth",
            "authorize_url": authorize_url,
        }

    # Fallback: auto-login with personal token
    return _login_with_token(DISCOGS_TOKEN)


# ---------------------------------------------------------------------------
# Step 2: GET /api/auth/discogs/callback
# ---------------------------------------------------------------------------


@router.get("/discogs/callback")
def discogs_callback(
    oauth_token: str = Query(None),
    oauth_verifier: str = Query(None),
    frontend_url: str = Query("http://localhost:5173"),
):
    """Handle OAuth 1.0a callback from Discogs.

    Exchanges request token + verifier for access token, creates user/session,
    redirects to frontend with session_token in URL fragment.
    """
    if not oauth_configured():
        raise HTTPException(501, "OAuth not configured. Use token-based auth.")

    if not oauth_token or not oauth_verifier:
        raise HTTPException(400, "Missing oauth_token or oauth_verifier")

    # Retrieve stored request_secret
    request_secret = _oauth_temp.pop(oauth_token, None)
    if not request_secret:
        raise HTTPException(400, "Unknown or expired oauth_token. Restart login flow.")

    # Exchange for access token
    try:
        access_token, access_secret = get_access_token(
            oauth_token, request_secret, oauth_verifier
        )
    except Exception as e:
        raise HTTPException(502, f"Failed to get access token: {e}")

    # Fetch user identity with OAuth credentials
    try:
        identity = fetch_identity_oauth(access_token, access_secret)
    except Exception as e:
        raise HTTPException(502, f"Failed to fetch identity: {e}")

    username = identity.get("username", "")
    if not username:
        raise HTTPException(502, "Could not retrieve Discogs username")

    # Fetch profile for avatar
    try:
        profile = fetch_user_profile_oauth(username, access_token, access_secret)
        avatar_url = profile.get("avatar_url", "")
    except Exception:
        avatar_url = ""

    # Upsert user in DB with OAuth tokens
    with get_user_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE discogs_username = ?", (username,)
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE users SET access_token = ?, access_secret = ?, avatar_url = ? "
                "WHERE discogs_username = ?",
                (access_token, access_secret, avatar_url, username),
            )
            user_id = existing["id"]
        else:
            cursor = conn.execute(
                "INSERT INTO users (discogs_username, access_token, access_secret, avatar_url) "
                "VALUES (?, ?, ?, ?)",
                (username, access_token, access_secret, avatar_url),
            )
            user_id = cursor.lastrowid
        conn.commit()

    # Create DB-backed session
    session_token = _create_session(user_id, username, avatar_url)

    # Redirect to frontend with session token in query
    redirect_url = f"{frontend_url}/auth/callback?session_token={session_token}"
    return RedirectResponse(url=redirect_url, status_code=302)


# ---------------------------------------------------------------------------
# MVP: Token-based login (personal token — single user / fallback mode)
# ---------------------------------------------------------------------------


@router.post("/discogs/login/token")
def discogs_login_token(token: str = Query(..., description="Discogs personal access token")):
    """Login with a Discogs personal access token (fallback mode).

    Users provide their own personal token from https://www.discogs.com/settings/developers
    """
    return _login_with_token(token)


def _login_with_token(token: str) -> dict:
    """Authenticate with a personal token, create/update user, return session."""
    if not token:
        raise HTTPException(400, "No Discogs token provided")

    try:
        identity = fetch_identity(token=token)
    except Exception as e:
        raise HTTPException(401, f"Invalid Discogs token: {e}")

    username = identity.get("username", "")
    if not username:
        raise HTTPException(401, "Could not retrieve Discogs username")

    # Fetch profile for avatar
    try:
        profile = fetch_user_profile(username, token=token)
        avatar_url = profile.get("avatar_url", "")
    except Exception:
        avatar_url = ""

    # Upsert user in DB
    with get_user_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE discogs_username = ?", (username,)
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE users SET access_token = ?, avatar_url = ? WHERE discogs_username = ?",
                (token, avatar_url, username),
            )
            user_id = existing["id"]
        else:
            cursor = conn.execute(
                "INSERT INTO users (discogs_username, access_token, avatar_url) VALUES (?, ?, ?)",
                (username, token, avatar_url),
            )
            user_id = cursor.lastrowid
        conn.commit()

    # Create DB-backed session
    session_token = _create_session(user_id, username, avatar_url)

    return {
        "mode": "token",
        "session_token": session_token,
        "user": {
            "id": user_id,
            "discogs_username": username,
            "avatar_url": avatar_url,
        },
    }


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------


@router.get("/me")
def get_current_user(session_token: str = Query(None)):
    """Return current user info if logged in."""
    user = _lookup_session(session_token)
    if not user:
        return {"authenticated": False, "user": None}

    return {
        "authenticated": True,
        "user": user,
    }


@router.post("/logout")
def logout(session_token: str = Query(...)):
    """Clear session by removing session_token from DB."""
    with get_user_db() as conn:
        conn.execute(
            "UPDATE users SET session_token = NULL WHERE session_token = ?",
            (session_token,),
        )
        conn.commit()
    return {"status": "ok"}
