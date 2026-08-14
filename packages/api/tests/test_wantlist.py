"""Wantlist routes — add/remove/ids with mocked Discogs calls."""

from unittest.mock import patch

import httpx
import pytest

from packages.api.user_db import get_user_db, init_user_db


@pytest.fixture()
def session_user():
    """Create a user with Discogs OAuth creds + a session token."""
    init_user_db()
    with get_user_db() as conn:
        conn.execute(
            "DELETE FROM users WHERE discogs_username = ?", ("wantlist_tester",)
        )
        cursor = conn.execute(
            "INSERT INTO users (discogs_username, access_token, access_secret, "
            "session_token) VALUES (?, ?, ?, ?)",
            ("wantlist_tester", "tok", "sec", "wantlist-session-token"),
        )
        user_id = cursor.lastrowid
        conn.execute(
            "DELETE FROM user_collection WHERE user_id = ?", (user_id,)
        )
        conn.commit()
    yield {"user_id": user_id, "session_token": "wantlist-session-token"}
    with get_user_db() as conn:
        conn.execute("DELETE FROM user_collection WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()


class TestWantlistAuth:
    def test_ids_requires_session(self, client):
        r = client.get("/api/wantlist/ids", params={"session_token": "bogus"})
        assert r.status_code == 401

    def test_add_requires_session(self, client):
        r = client.put("/api/wantlist/12345", params={"session_token": "bogus"})
        assert r.status_code == 401


class TestWantlistAddRemove:
    def test_add_then_ids_then_remove(self, client, session_user):
        token = session_user["session_token"]

        with patch(
            "packages.api.routes.wantlist.add_want", return_value={"id": 999}
        ) as mock_add:
            r = client.put("/api/wantlist/999", params={"session_token": token})
        assert r.status_code == 200
        assert r.json() == {"status": "added", "release_id": 999}
        mock_add.assert_called_once_with("wantlist_tester", 999, "tok", "sec")

        r = client.get("/api/wantlist/ids", params={"session_token": token})
        assert r.status_code == 200
        assert 999 in r.json()["ids"]

        with patch("packages.api.routes.wantlist.remove_want") as mock_rm:
            r = client.delete("/api/wantlist/999", params={"session_token": token})
        assert r.status_code == 200
        assert r.json() == {"status": "removed", "release_id": 999}
        mock_rm.assert_called_once_with("wantlist_tester", 999, "tok", "sec")

        r = client.get("/api/wantlist/ids", params={"session_token": token})
        assert 999 not in r.json()["ids"]

    def test_remove_idempotent_on_discogs_404(self, client, session_user):
        token = session_user["session_token"]
        resp_404 = httpx.Response(
            404, request=httpx.Request("DELETE", "https://api.discogs.com/x")
        )
        err = httpx.HTTPStatusError("404", request=resp_404.request, response=resp_404)

        with patch("packages.api.routes.wantlist.remove_want", side_effect=err):
            r = client.delete("/api/wantlist/424242", params={"session_token": token})
        assert r.status_code == 200
        assert r.json()["status"] == "removed"

    def test_add_maps_discogs_401_to_reauth(self, client, session_user):
        token = session_user["session_token"]
        resp_401 = httpx.Response(
            401, request=httpx.Request("PUT", "https://api.discogs.com/x")
        )
        err = httpx.HTTPStatusError("401", request=resp_401.request, response=resp_401)

        with patch("packages.api.routes.wantlist.add_want", side_effect=err):
            r = client.put("/api/wantlist/5", params={"session_token": token})
        assert r.status_code == 401
        assert "Reconnect" in r.json()["detail"]


class TestOAuthHeader:
    def test_plaintext_header_shape(self):
        from packages.api import discogs_client as dc

        with (
            patch.object(dc, "DISCOGS_CONSUMER_KEY", "ckey"),
            patch.object(dc, "DISCOGS_CONSUMER_SECRET", "csecret"),
        ):
            header = dc._oauth_header(token="atok", token_secret="asec")
        assert header.startswith("OAuth ")
        assert 'oauth_consumer_key="ckey"' in header
        assert 'oauth_signature="csecret%26asec"' in header
        assert 'oauth_signature_method="PLAINTEXT"' in header
        assert 'oauth_token="atok"' in header
