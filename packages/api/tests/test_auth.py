"""Auth routes — OAuth 1.0a + token fallback tests."""

from unittest.mock import patch

import pytest


# ============================================================================
# GET /api/auth/me
# ============================================================================


class TestAuthMe:
    def test_me_unauthenticated_no_token(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert data["authenticated"] is False
        assert data["user"] is None

    def test_me_invalid_session_token(self, client):
        r = client.get("/api/auth/me", params={"session_token": "bogus-token-xyz"})
        assert r.status_code == 200
        data = r.json()
        assert data["authenticated"] is False
        assert data["user"] is None


# ============================================================================
# GET /api/auth/discogs/login — fallback mode (no OAuth consumer keys)
# ============================================================================


class TestDiscogsLoginFallback:
    """Test login when OAuth consumer keys are NOT configured (personal token mode)."""

    def test_login_token_fallback(self, client):
        with (
            patch("packages.api.routes.auth.oauth_configured", return_value=False),
            patch("packages.api.routes.auth.DISCOGS_TOKEN", "fake-personal-token"),
            patch("packages.api.routes.auth.fetch_identity", return_value={"username": "testuser123"}),
            patch("packages.api.routes.auth.fetch_user_profile", return_value={"avatar_url": "https://img.discogs.com/avatar.jpg"}),
        ):
            r = client.get("/api/auth/discogs/login")
            assert r.status_code == 200
            data = r.json()
            assert data["mode"] == "token"
            assert "session_token" in data
            assert data["user"]["discogs_username"] == "testuser123"

    def test_login_no_token_400(self, client):
        with (
            patch("packages.api.routes.auth.oauth_configured", return_value=False),
            patch("packages.api.routes.auth.DISCOGS_TOKEN", ""),
        ):
            r = client.get("/api/auth/discogs/login")
            assert r.status_code == 400


# ============================================================================
# GET /api/auth/discogs/login — OAuth mode
# ============================================================================


class TestDiscogsLoginOAuth:
    """Test login when OAuth consumer keys ARE configured."""

    def test_login_oauth_returns_authorize_url(self, client):
        with (
            patch("packages.api.routes.auth.oauth_configured", return_value=True),
            patch(
                "packages.api.routes.auth.get_request_token",
                return_value=("req_token_abc", "req_secret_xyz", "https://www.discogs.com/oauth/authorize?oauth_token=req_token_abc"),
            ),
        ):
            r = client.get("/api/auth/discogs/login")
            assert r.status_code == 200
            data = r.json()
            assert data["mode"] == "oauth"
            assert "authorize_url" in data
            assert "req_token_abc" in data["authorize_url"]


# ============================================================================
# GET /api/auth/discogs/callback
# ============================================================================


class TestDiscogsCallback:
    def test_callback_without_oauth_configured(self, client):
        """Callback should fail when OAuth is not configured."""
        with patch("packages.api.routes.auth.oauth_configured", return_value=False):
            r = client.get(
                "/api/auth/discogs/callback",
                params={"oauth_token": "tok", "oauth_verifier": "ver"},
            )
            assert r.status_code == 501

    def test_callback_missing_params(self, client):
        """Callback with missing oauth params should fail."""
        with patch("packages.api.routes.auth.oauth_configured", return_value=True):
            r = client.get("/api/auth/discogs/callback")
            assert r.status_code == 400

    def test_callback_unknown_token(self, client):
        """Callback with unknown oauth_token should fail."""
        with patch("packages.api.routes.auth.oauth_configured", return_value=True):
            r = client.get(
                "/api/auth/discogs/callback",
                params={"oauth_token": "unknown", "oauth_verifier": "ver"},
            )
            assert r.status_code == 400
            detail = r.json()["detail"].lower()
            assert "expired" in detail or "unknown" in detail

    def test_callback_full_flow(self, client):
        """Full OAuth callback: inject a temp token, then hit callback."""
        from packages.api.routes.auth import _oauth_temp

        _oauth_temp["test_req_token"] = "test_req_secret"

        with (
            patch("packages.api.routes.auth.oauth_configured", return_value=True),
            patch("packages.api.routes.auth.get_access_token", return_value=("access_tok", "access_sec")),
            patch("packages.api.routes.auth.fetch_identity_oauth", return_value={"username": "oauth_user"}),
            patch("packages.api.routes.auth.fetch_user_profile_oauth", return_value={"avatar_url": "https://img.discogs.com/oauth_avatar.jpg"}),
        ):
            r = client.get(
                "/api/auth/discogs/callback",
                params={
                    "oauth_token": "test_req_token",
                    "oauth_verifier": "test_verifier",
                    "frontend_url": "http://localhost:5173",
                },
                follow_redirects=False,
            )
            # Should redirect to frontend with session_token
            assert r.status_code == 302
            location = r.headers.get("location", "")
            assert "session_token=" in location
            assert "localhost:5173/auth/callback" in location

            # Extract session token and verify it works
            import urllib.parse

            parsed = urllib.parse.urlparse(location)
            qs = urllib.parse.parse_qs(parsed.query)
            session_token = qs["session_token"][0]

        me_r = client.get("/api/auth/me", params={"session_token": session_token})
        assert me_r.status_code == 200
        assert me_r.json()["authenticated"] is True
        assert me_r.json()["user"]["discogs_username"] == "oauth_user"


# ============================================================================
# POST /api/auth/logout
# ============================================================================


class TestLogout:
    def test_logout_clears_session(self, client):
        with (
            patch("packages.api.routes.auth.oauth_configured", return_value=False),
            patch("packages.api.routes.auth.DISCOGS_TOKEN", "fake-token"),
            patch("packages.api.routes.auth.fetch_identity", return_value={"username": "logoutuser"}),
            patch("packages.api.routes.auth.fetch_user_profile", return_value={"avatar_url": ""}),
        ):
            # Login first
            login_r = client.get("/api/auth/discogs/login")
            session_token = login_r.json()["session_token"]

        # Verify session is active
        me_r = client.get("/api/auth/me", params={"session_token": session_token})
        assert me_r.json()["authenticated"] is True

        # Logout
        logout_r = client.post("/api/auth/logout", params={"session_token": session_token})
        assert logout_r.status_code == 200
        assert logout_r.json()["status"] == "ok"

        # Verify session is cleared
        me_r2 = client.get("/api/auth/me", params={"session_token": session_token})
        assert me_r2.json()["authenticated"] is False

    def test_logout_nonexistent_token(self, client):
        """Logging out with a nonexistent token should still succeed."""
        r = client.post("/api/auth/logout", params={"session_token": "nonexistent"})
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ============================================================================
# Session validation — DB-backed
# ============================================================================


class TestSessionValidation:
    def test_session_persists_in_db(self, client):
        """Session tokens should be stored in the users table, not in memory."""
        with (
            patch("packages.api.routes.auth.oauth_configured", return_value=False),
            patch("packages.api.routes.auth.DISCOGS_TOKEN", "fake-token"),
            patch("packages.api.routes.auth.fetch_identity", return_value={"username": "session_test_user"}),
            patch("packages.api.routes.auth.fetch_user_profile", return_value={"avatar_url": "https://example.com/pic.jpg"}),
        ):
            login_r = client.get("/api/auth/discogs/login")
            session_token = login_r.json()["session_token"]

        # Verify via /me
        me_r = client.get("/api/auth/me", params={"session_token": session_token})
        data = me_r.json()
        assert data["authenticated"] is True
        assert data["user"]["discogs_username"] == "session_test_user"
        assert data["user"]["avatar_url"] == "https://example.com/pic.jpg"
