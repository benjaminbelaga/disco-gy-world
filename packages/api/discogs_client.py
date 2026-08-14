"""Discogs API client with rate limiting and OAuth 1.0a support."""

import os
import secrets as _secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import parse_qsl, quote

import httpx

# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

_ENV_FILE = Path.home() / ".credentials" / "yoyaku" / "api-keys" / "discogs.env"


def _load_env() -> dict[str, str]:
    """Parse key=value from discogs.env."""
    env: dict[str, str] = {}
    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


_env = _load_env()

# discogs.env carries the token under YOYAKU_DISCOGS_PERSONAL_TOKEN; there is no
# bare DISCOGS_TOKEN key in it, on this machine or on the server. Without the
# fallback every call goes out unauthenticated, which Discogs rate-limits to
# 25 req/min instead of 60 — and the RateLimiter below is configured for 58, so
# we would have been silently over budget rather than under it.
DISCOGS_TOKEN = (
    os.environ.get("DISCOGS_TOKEN")
    or _env.get("DISCOGS_TOKEN", "")
    or _env.get("YOYAKU_DISCOGS_PERSONAL_TOKEN", "")
)
DISCOGS_CONSUMER_KEY = os.environ.get("DISCOGS_CONSUMER_KEY") or _env.get(
    "DISCOGS_CONSUMER_KEY", ""
)
DISCOGS_CONSUMER_SECRET = os.environ.get("DISCOGS_CONSUMER_SECRET") or _env.get(
    "DISCOGS_CONSUMER_SECRET", ""
)
DISCOGS_USER_AGENT = (
    os.environ.get("DISCOGS_USER_AGENT")
    or _env.get("DISCOGS_USER_AGENT", "DiscoWorld/2.0 +https://github.com/benjaminbelaga/discoworld")
)
DISCOGS_API_URL = "https://api.discogs.com"

# OAuth 1.0a endpoints
REQUEST_TOKEN_URL = "https://api.discogs.com/oauth/request_token"
AUTHORIZE_URL = "https://www.discogs.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://api.discogs.com/oauth/access_token"

# ---------------------------------------------------------------------------
# Rate limiter — 60 req/min for authenticated requests
# ---------------------------------------------------------------------------


@dataclass
class RateLimiter:
    """Simple sliding-window rate limiter."""

    max_requests: int = 58  # Leave 2 margin
    window_seconds: float = 60.0
    _timestamps: list[float] = field(default_factory=list)
    _lock: Lock = field(default_factory=Lock)

    def wait(self) -> None:
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            self._timestamps = [t for t in self._timestamps if t > cutoff]
            if len(self._timestamps) >= self.max_requests:
                sleep_time = self._timestamps[0] - cutoff + 0.1
                time.sleep(sleep_time)
            self._timestamps.append(time.time())


_limiter = RateLimiter()

# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


def _headers(user_agent: str | None = None) -> dict[str, str]:
    return {
        "User-Agent": user_agent or DISCOGS_USER_AGENT,
        "Accept": "application/vnd.discogs.v2.discogs+json",
    }


def api_get(
    path: str,
    params: dict[str, Any] | None = None,
    token: str | None = None,
) -> dict:
    """GET from Discogs API using personal token auth.

    For MVP, we use the personal access token. OAuth 1.0a can be added later
    when consumer key/secret are available.
    """
    _limiter.wait()
    auth_token = token or DISCOGS_TOKEN
    url = f"{DISCOGS_API_URL}{path}"
    all_params = {}
    # Only include token param if we actually have one (public API works without)
    if auth_token:
        all_params["token"] = auth_token
    if params:
        all_params.update(params)

    resp = httpx.get(url, params=all_params, headers=_headers(), timeout=30.0)
    resp.raise_for_status()
    return resp.json()


def fetch_collection(
    username: str, token: str | None = None, page: int = 1, per_page: int = 100
) -> dict:
    """Fetch a user's collection folders/0/releases (all folders)."""
    return api_get(
        f"/users/{username}/collection/folders/0/releases",
        params={"page": page, "per_page": per_page, "sort": "added", "sort_order": "desc"},
        token=token,
    )


def fetch_all_collection(username: str, token: str | None = None) -> list[dict]:
    """Fetch all pages of a user's collection."""
    all_releases: list[dict] = []
    page = 1
    while True:
        data = fetch_collection(username, token=token, page=page, per_page=100)
        releases = data.get("releases", [])
        all_releases.extend(releases)
        pagination = data.get("pagination", {})
        if page >= pagination.get("pages", 1):
            break
        page += 1
    return all_releases


def fetch_wantlist(
    username: str, token: str | None = None, page: int = 1, per_page: int = 100
) -> dict:
    """Fetch a user's wantlist."""
    return api_get(
        f"/users/{username}/wants",
        params={"page": page, "per_page": per_page},
        token=token,
    )


def fetch_all_wantlist(username: str, token: str | None = None) -> list[dict]:
    """Fetch all pages of a user's wantlist."""
    all_wants: list[dict] = []
    page = 1
    while True:
        data = fetch_wantlist(username, token=token, page=page, per_page=100)
        wants = data.get("wants", [])
        all_wants.extend(wants)
        pagination = data.get("pagination", {})
        if page >= pagination.get("pages", 1):
            break
        page += 1
    return all_wants


def fetch_identity(token: str | None = None) -> dict:
    """Fetch the identity of the authenticated user."""
    return api_get("/oauth/identity", token=token)


def fetch_user_profile(username: str, token: str | None = None) -> dict:
    """Fetch a user's public profile."""
    return api_get(f"/users/{username}", token=token)


# ---------------------------------------------------------------------------
# OAuth 1.0a helpers — requires DISCOGS_CONSUMER_KEY & DISCOGS_CONSUMER_SECRET
#
# Discogs officially supports the PLAINTEXT signature method over HTTPS
# (oauth_signature = "consumer_secret&token_secret"), which lets us sign
# requests with stdlib + httpx only. The previous implementation imported
# requests_oauthlib lazily — a dependency that was absent from
# requirements.txt AND from the production host, so every OAuth login
# 502'd at import time.
# ---------------------------------------------------------------------------


def oauth_configured() -> bool:
    """Return True if OAuth 1.0a consumer credentials are set."""
    return bool(DISCOGS_CONSUMER_KEY and DISCOGS_CONSUMER_SECRET)


def _oauth_header(
    token: str = "",
    token_secret: str = "",
    callback: str | None = None,
    verifier: str | None = None,
) -> str:
    """Build a PLAINTEXT-signed OAuth 1.0a Authorization header."""
    parts: dict[str, str] = {
        "oauth_consumer_key": DISCOGS_CONSUMER_KEY,
        "oauth_nonce": _secrets.token_hex(16),
        "oauth_signature": f"{DISCOGS_CONSUMER_SECRET}&{token_secret}",
        "oauth_signature_method": "PLAINTEXT",
        "oauth_timestamp": str(int(time.time())),
    }
    if token:
        parts["oauth_token"] = token
    if callback:
        parts["oauth_callback"] = callback
    if verifier:
        parts["oauth_verifier"] = verifier
    return "OAuth " + ", ".join(
        f'{k}="{quote(v, safe="")}"' for k, v in parts.items()
    )


def oauth_request(
    method: str,
    url: str,
    access_token: str = "",
    access_secret: str = "",
    callback: str | None = None,
    verifier: str | None = None,
) -> httpx.Response:
    """Perform an OAuth 1.0a signed request against Discogs."""
    _limiter.wait()
    headers = _headers()
    headers["Authorization"] = _oauth_header(
        token=access_token,
        token_secret=access_secret,
        callback=callback,
        verifier=verifier,
    )
    resp = httpx.request(method, url, headers=headers, timeout=30.0)
    resp.raise_for_status()
    return resp


def get_request_token(callback_url: str) -> tuple[str, str, str]:
    """Step 1: Get a request token from Discogs.

    Returns (request_token, request_secret, authorize_url).
    """
    resp = oauth_request("GET", REQUEST_TOKEN_URL, callback=callback_url)
    data = dict(parse_qsl(resp.text))
    request_token = data["oauth_token"]
    request_secret = data["oauth_token_secret"]
    authorize_url = f"{AUTHORIZE_URL}?oauth_token={request_token}"
    return request_token, request_secret, authorize_url


def get_access_token(
    request_token: str, request_secret: str, oauth_verifier: str
) -> tuple[str, str]:
    """Step 2: Exchange request token + verifier for access token.

    Returns (access_token, access_secret).
    """
    resp = oauth_request(
        "POST",
        ACCESS_TOKEN_URL,
        access_token=request_token,
        access_secret=request_secret,
        verifier=oauth_verifier,
    )
    data = dict(parse_qsl(resp.text))
    return data["oauth_token"], data["oauth_token_secret"]


def fetch_identity_oauth(access_token: str, access_secret: str) -> dict:
    """Fetch identity using OAuth 1.0a credentials (not personal token)."""
    resp = oauth_request(
        "GET", f"{DISCOGS_API_URL}/oauth/identity", access_token, access_secret
    )
    return resp.json()


def fetch_user_profile_oauth(
    username: str, access_token: str, access_secret: str
) -> dict:
    """Fetch user profile using OAuth 1.0a credentials."""
    resp = oauth_request(
        "GET", f"{DISCOGS_API_URL}/users/{username}", access_token, access_secret
    )
    return resp.json()


# ---------------------------------------------------------------------------
# Wantlist writes — OAuth session or personal token
# ---------------------------------------------------------------------------


def _authed_request(
    method: str, path: str, access_token: str, access_secret: str = ""
) -> httpx.Response:
    """Authenticated Discogs call. OAuth 1.0a when the user has an access
    secret (OAuth login), personal-token auth otherwise (token login)."""
    url = f"{DISCOGS_API_URL}{path}"
    if access_secret:
        return oauth_request(method, url, access_token, access_secret)
    _limiter.wait()
    headers = _headers()
    headers["Authorization"] = f"Discogs token={access_token}"
    resp = httpx.request(method, url, headers=headers, timeout=30.0)
    resp.raise_for_status()
    return resp


def add_want(
    username: str, release_id: int, access_token: str, access_secret: str = ""
) -> dict:
    """Add a release to the user's Discogs wantlist."""
    resp = _authed_request(
        "PUT", f"/users/{username}/wants/{release_id}", access_token, access_secret
    )
    try:
        return resp.json()
    except ValueError:
        return {}


def remove_want(
    username: str, release_id: int, access_token: str, access_secret: str = ""
) -> None:
    """Remove a release from the user's Discogs wantlist (204 on success)."""
    _authed_request(
        "DELETE", f"/users/{username}/wants/{release_id}", access_token, access_secret
    )
