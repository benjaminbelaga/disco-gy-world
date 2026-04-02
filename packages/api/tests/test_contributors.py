"""Tests for the contributor recognition system."""

import time
import pytest
from fastapi.testclient import TestClient
from packages.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Stats (empty state)
# ---------------------------------------------------------------------------

class TestStats:
    def test_stats_empty(self, client):
        r = client.get("/api/contributors/stats")
        assert r.status_code == 200
        data = r.json()
        assert "total_contributors" in data
        assert "total_contributions" in data
        assert "most_active_type" in data
        assert "contributions_today" in data


# ---------------------------------------------------------------------------
# Contribute
# ---------------------------------------------------------------------------

class TestContribute:
    def test_contribute_genre_edit(self, client):
        r = client.post("/api/contributors/alice/contribute", json={
            "type": "genre_edit",
            "detail": "Fixed ambient techno classification",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data["username"] == "alice"
        assert data["points"] == 10  # default for genre_edit

    def test_contribute_bug_report(self, client):
        r = client.post("/api/contributors/bob/contribute", json={
            "type": "bug_report",
            "detail": "Search returns no results for 'dub'",
        })
        assert r.status_code == 200
        assert r.json()["points"] == 2

    def test_contribute_custom_points(self, client):
        r = client.post("/api/contributors/alice/contribute", json={
            "type": "youtube_link",
            "detail": "Added DJ set link",
            "points": 5,
        })
        assert r.status_code == 200
        assert r.json()["points"] == 5  # custom override

    def test_contribute_invalid_type(self, client):
        r = client.post("/api/contributors/alice/contribute", json={
            "type": "invalid_type",
            "detail": "nope",
        })
        assert r.status_code == 400
        assert "Invalid type" in r.json()["detail"]

    def test_contribute_all_types(self, client):
        """Ensure all valid contribution types are accepted."""
        for ctype, expected_points in [
            ("path_created", 5),
            ("data_enrichment", 5),
        ]:
            r = client.post("/api/contributors/charlie/contribute", json={
                "type": ctype,
                "detail": f"Test {ctype}",
            })
            assert r.status_code == 200
            assert r.json()["points"] == expected_points


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

class TestProfile:
    def test_get_profile(self, client):
        # alice contributed twice above
        r = client.get("/api/contributors/alice")
        assert r.status_code == 200
        data = r.json()
        assert data["profile"]["username"] == "alice"
        assert data["profile"]["total_points"] >= 10
        assert len(data["breakdown"]) > 0
        assert len(data["recent"]) > 0

    def test_get_profile_not_found(self, client):
        r = client.get("/api/contributors/nonexistent_user_xyz")
        assert r.status_code == 404

    def test_profile_breakdown_structure(self, client):
        r = client.get("/api/contributors/alice")
        data = r.json()
        for entry in data["breakdown"]:
            assert "type" in entry
            assert "count" in entry
            assert "points" in entry

    def test_profile_recent_structure(self, client):
        r = client.get("/api/contributors/alice")
        data = r.json()
        for entry in data["recent"]:
            assert "id" in entry
            assert "type" in entry
            assert "detail" in entry
            assert "points" in entry
            assert "created_at" in entry


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

class TestLeaderboard:
    def test_leaderboard_default(self, client):
        r = client.get("/api/contributors/leaderboard")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check sorted by points descending
        points = [e["total_points"] for e in data]
        assert points == sorted(points, reverse=True)

    def test_leaderboard_structure(self, client):
        r = client.get("/api/contributors/leaderboard")
        entry = r.json()[0]
        assert "username" in entry
        assert "total_points" in entry
        assert "contributions_count" in entry
        assert "top_type" in entry
        assert "rank" in entry
        assert entry["rank"] == 1

    def test_leaderboard_with_limit(self, client):
        r = client.get("/api/contributors/leaderboard?limit=2")
        assert r.status_code == 200
        assert len(r.json()) <= 2

    def test_leaderboard_period_week(self, client):
        r = client.get("/api/contributors/leaderboard?period=week")
        assert r.status_code == 200

    def test_leaderboard_period_month(self, client):
        r = client.get("/api/contributors/leaderboard?period=month")
        assert r.status_code == 200

    def test_leaderboard_invalid_period(self, client):
        r = client.get("/api/contributors/leaderboard?period=year")
        assert r.status_code == 422  # validation error


# ---------------------------------------------------------------------------
# Stats (with data)
# ---------------------------------------------------------------------------

class TestStatsWithData:
    def test_stats_populated(self, client):
        r = client.get("/api/contributors/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["total_contributors"] >= 2  # alice + bob at minimum
        assert data["total_contributions"] >= 3
        assert data["most_active_type"] is not None
        assert data["contributions_today"] >= 3
