"""Discogs API client with rate limiting and OAuth 1.0a support."""

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

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

DISCOGS_TOKEN = os.environ.get("DISCOGS_TOKEN") or _env.get("DISCOGS_TOKEN", "")
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
# ---------------------------------------------------------------------------


def oauth_configured() -> bool:
    """Return True if OAuth 1.0a consumer credentials are set."""
    return bool(DISCOGS_CONSUMER_KEY and DISCOGS_CONSUMER_SECRET)


def get_request_token(callback_url: str) -> tuple[str, str, str]:
    """Step 1: Get a request token from Discogs.

    Returns (request_token, request_secret, authorize_url).
    """
    from requests_oauthlib import OAuth1Session

    oauth = OAuth1Session(
        DISCOGS_CONSUMER_KEY,
        client_secret=DISCOGS_CONSUMER_SECRET,
        callback_uri=callback_url,
    )
    resp = oauth.fetch_request_token(REQUEST_TOKEN_URL)
    request_token = resp["oauth_token"]
    request_secret = resp["oauth_token_secret"]
    authorize_url = f"{AUTHORIZE_URL}?oauth_token={request_token}"
    return request_token, request_secret, authorize_url


def get_access_token(
    request_token: str, request_secret: str, oauth_verifier: str
) -> tuple[str, str]:
    """Step 2: Exchange request token + verifier for access token.

    Returns (access_token, access_secret).
    """
    from requests_oauthlib import OAuth1Session

    oauth = OAuth1Session(
        DISCOGS_CONSUMER_KEY,
        client_secret=DISCOGS_CONSUMER_SECRET,
        resource_owner_key=request_token,
        resource_owner_secret=request_secret,
        verifier=oauth_verifier,
    )
    resp = oauth.fetch_access_token(ACCESS_TOKEN_URL)
    return resp["oauth_token"], resp["oauth_token_secret"]


def fetch_identity_oauth(access_token: str, access_secret: str) -> dict:
    """Fetch identity using OAuth 1.0a credentials (not personal token)."""
    from requests_oauthlib import OAuth1Session

    oauth = OAuth1Session(
        DISCOGS_CONSUMER_KEY,
        client_secret=DISCOGS_CONSUMER_SECRET,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
    )
    resp = oauth.get(
        f"{DISCOGS_API_URL}/oauth/identity",
        headers=_headers(),
    )
    resp.raise_for_status()
    return resp.json()


def fetch_user_profile_oauth(
    username: str, access_token: str, access_secret: str
) -> dict:
    """Fetch user profile using OAuth 1.0a credentials."""
    from requests_oauthlib import OAuth1Session

    oauth = OAuth1Session(
        DISCOGS_CONSUMER_KEY,
        client_secret=DISCOGS_CONSUMER_SECRET,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
    )
    resp = oauth.get(
        f"{DISCOGS_API_URL}/users/{username}",
        headers=_headers(),
    )
    resp.raise_for_status()
    return resp.json()
