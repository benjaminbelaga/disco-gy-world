"""Tests for genre editing API endpoints."""
import pytest
from fastapi.testclient import TestClient
from packages.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestCreateEdit:
    def test_create_valid_edit(self, client):
        resp = client.post("/api/genre-edits", json={
            "genre_slug": "techno",
            "field": "description",
            "new_value": "Updated techno description",
            "reason": "More accurate",
            "author": "testuser",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["genre_slug"] == "techno"
        assert data["field"] == "description"
        assert data["status"] == "pending"
        assert data["id"] > 0

    def test_create_edit_invalid_field(self, client):
        resp = client.post("/api/genre-edits", json={
            "genre_slug": "techno",
            "field": "invalid_field",
            "new_value": "test",
        })
        assert resp.status_code == 422

    def test_create_edit_minimal(self, client):
        resp = client.post("/api/genre-edits", json={
            "genre_slug": "house",
            "field": "aka",
            "new_value": "House Music",
        })
        assert resp.status_code == 200
        assert resp.json()["author"] == "anonymous"


class TestListEdits:
    def test_list_all(self, client):
        resp = client.get("/api/genre-edits")
        assert resp.status_code == 200
        data = resp.json()
        assert "edits" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_filter_by_status(self, client):
        resp = client.get("/api/genre-edits?status=pending")
        assert resp.status_code == 200
        for edit in resp.json()["edits"]:
            assert edit["status"] == "pending"

    def test_filter_by_genre(self, client):
        resp = client.get("/api/genre-edits?genre_slug=techno")
        assert resp.status_code == 200
        for edit in resp.json()["edits"]:
            assert edit["genre_slug"] == "techno"

    def test_pagination(self, client):
        resp = client.get("/api/genre-edits?limit=1&offset=0")
        assert resp.status_code == 200
        assert len(resp.json()["edits"]) <= 1


class TestGetEdit:
    def test_get_existing(self, client):
        # Create an edit first
        create = client.post("/api/genre-edits", json={
            "genre_slug": "ambient",
            "field": "emerged",
            "new_value": "early 80s",
            "author": "tester",
        })
        edit_id = create.json()["id"]

        resp = client.get(f"/api/genre-edits/{edit_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == edit_id
        assert "votes" in data
        assert "approve_count" in data

    def test_get_not_found(self, client):
        resp = client.get("/api/genre-edits/999999")
        assert resp.status_code == 404


class TestVoting:
    def test_vote_approve(self, client):
        create = client.post("/api/genre-edits", json={
            "genre_slug": "dnb",
            "field": "description",
            "new_value": "Fast breakbeats",
            "author": "a",
        })
        edit_id = create.json()["id"]

        resp = client.post(f"/api/genre-edits/{edit_id}/vote", json={
            "vote": "approve",
            "voter": "voter1",
        })
        assert resp.status_code == 200
        assert resp.json()["approve_count"] == 1

    def test_vote_reject(self, client):
        create = client.post("/api/genre-edits", json={
            "genre_slug": "trance",
            "field": "aka",
            "new_value": "Euro Trance",
            "author": "b",
        })
        edit_id = create.json()["id"]

        resp = client.post(f"/api/genre-edits/{edit_id}/vote", json={
            "vote": "reject",
            "voter": "voter1",
        })
        assert resp.status_code == 200
        assert resp.json()["reject_count"] == 1

    def test_duplicate_vote_rejected(self, client):
        create = client.post("/api/genre-edits", json={
            "genre_slug": "house",
            "field": "scene",
            "new_value": "Deep House",
            "author": "c",
        })
        edit_id = create.json()["id"]

        client.post(f"/api/genre-edits/{edit_id}/vote", json={"vote": "approve", "voter": "v1"})
        resp = client.post(f"/api/genre-edits/{edit_id}/vote", json={"vote": "approve", "voter": "v1"})
        assert resp.status_code == 409

    def test_auto_approve_threshold(self, client):
        create = client.post("/api/genre-edits", json={
            "genre_slug": "electro",
            "field": "description",
            "new_value": "Robot funk",
            "author": "d",
        })
        edit_id = create.json()["id"]

        for i in range(3):
            resp = client.post(f"/api/genre-edits/{edit_id}/vote", json={
                "vote": "approve", "voter": f"auto_voter_{i}",
            })

        assert resp.json()["status"] == "approved"

    def test_vote_on_closed_edit_rejected(self, client):
        # Create and auto-approve an edit
        create = client.post("/api/genre-edits", json={
            "genre_slug": "idm",
            "field": "aka",
            "new_value": "Braindance",
            "author": "e",
        })
        edit_id = create.json()["id"]
        for i in range(3):
            client.post(f"/api/genre-edits/{edit_id}/vote", json={"vote": "approve", "voter": f"closer_{i}"})

        resp = client.post(f"/api/genre-edits/{edit_id}/vote", json={"vote": "reject", "voter": "late_voter"})
        assert resp.status_code == 400

    def test_vote_not_found(self, client):
        resp = client.post("/api/genre-edits/999999/vote", json={"vote": "approve", "voter": "x"})
        assert resp.status_code == 404


class TestStats:
    def test_stats_response(self, client):
        resp = client.get("/api/genre-edits/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "pending" in data
        assert "approved" in data
        assert "rejected" in data
        assert "top_contributors" in data
        assert "top_genres" in data
