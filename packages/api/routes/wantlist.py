"""Wantlist routes — add/remove releases on the user's Discogs wantlist.

The heart button in the player talks to these endpoints. Discogs is the
source of truth; user_collection rows with source='wantlist' are a local
mirror kept in step so the UI can paint heart states without hitting the
Discogs API on every page load.
"""

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query

from ..discogs_client import add_want, remove_want
from ..user_db import get_user_db
from .auth import _lookup_session

router = APIRouter(prefix="/api/wantlist", tags=["wantlist"])


def _get_discogs_auth(session_token: str | None) -> dict:
    """Resolve session -> Discogs credentials. Raises 401 when absent."""
    user = _lookup_session(session_token)
    if not user:
        raise HTTPException(401, "Not authenticated. Provide a valid session_token.")

    with get_user_db() as conn:
        row = conn.execute(
            "SELECT access_token, access_secret FROM users WHERE id = ?",
            (user["user_id"],),
        ).fetchone()

    if not row or not row["access_token"]:
        raise HTTPException(
            401, "No Discogs credentials on file. Reconnect your Discogs account."
        )

    return {
        "user_id": user["user_id"],
        "username": user["discogs_username"],
        "access_token": row["access_token"],
        "access_secret": row["access_secret"] or "",
    }


def _discogs_error(e: Exception) -> HTTPException:
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code in (401, 403):
            return HTTPException(
                401, "Discogs rejected our credentials. Reconnect your account."
            )
        if code == 404:
            return HTTPException(404, "Release not found on Discogs.")
        if code == 429:
            return HTTPException(429, "Discogs rate limit reached. Retry in a minute.")
    return HTTPException(502, f"Discogs API error: {e}")


@router.get("/ids")
def wantlist_ids(session_token: str = Query(...)):
    """Return the Discogs release ids in the user's local wantlist mirror."""
    auth = _get_discogs_auth(session_token)
    with get_user_db() as conn:
        rows = conn.execute(
            "SELECT discogs_release_id FROM user_collection "
            "WHERE user_id = ? AND source = 'wantlist'",
            (auth["user_id"],),
        ).fetchall()
    return {"ids": [r["discogs_release_id"] for r in rows]}


@router.put("/{release_id}")
def wantlist_add(release_id: int, session_token: str = Query(...)):
    """Add a release to the user's Discogs wantlist + local mirror."""
    auth = _get_discogs_auth(session_token)
    try:
        add_want(
            auth["username"], release_id, auth["access_token"], auth["access_secret"]
        )
    except Exception as e:
        raise _discogs_error(e)

    now = datetime.now(timezone.utc).isoformat()
    with get_user_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO user_collection
               (user_id, release_id, discogs_release_id, rating, date_added, source)
               VALUES (?, ?, ?, 0, ?, 'wantlist')""",
            (auth["user_id"], release_id, release_id, now),
        )
        conn.commit()

    return {"status": "added", "release_id": release_id}


@router.delete("/{release_id}")
def wantlist_remove(release_id: int, session_token: str = Query(...)):
    """Remove a release from the user's Discogs wantlist + local mirror."""
    auth = _get_discogs_auth(session_token)
    try:
        remove_want(
            auth["username"], release_id, auth["access_token"], auth["access_secret"]
        )
    except httpx.HTTPStatusError as e:
        # Already absent on Discogs — treat the removal as idempotent
        if e.response.status_code != 404:
            raise _discogs_error(e)
    except Exception as e:
        raise _discogs_error(e)

    with get_user_db() as conn:
        conn.execute(
            "DELETE FROM user_collection "
            "WHERE user_id = ? AND discogs_release_id = ? AND source = 'wantlist'",
            (auth["user_id"], release_id),
        )
        conn.commit()

    return {"status": "removed", "release_id": release_id}
