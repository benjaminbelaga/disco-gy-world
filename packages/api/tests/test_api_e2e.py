"""DiscoWorld API — comprehensive E2E test suite."""

import pytest


# ============================================================================
# 1. GET /api/health
# ============================================================================


class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "genres" in data
        assert isinstance(data["genres"], int)
        assert data["genres"] > 0

    def test_health_genre_count(self, client):
        r = client.get("/api/health")
        assert r.json()["genres"] == 166


# ============================================================================
# 2. GET /api/genres
# ============================================================================


class TestGenres:
    def test_list_genres(self, client):
        r = client.get("/api/genres")
        assert r.status_code == 200
        data = r.json()
        assert "meta" in data
        assert "genres" in data
        assert len(data["genres"]) == 166

    def test_genres_meta_keys(self, client):
        r = client.get("/api/genres")
        meta = r.json()["meta"]
        assert "genreCount" in meta

    def test_genre_item_structure(self, client):
        r = client.get("/api/genres")
        genre = r.json()["genres"][0]
        for key in ("slug", "name", "scene", "biome", "color"):
            assert key in genre, f"Missing key: {key}"


# ============================================================================
# 3. GET /api/genres/{slug}
# ============================================================================


class TestGenreBySlug:
    def test_valid_slug(self, client):
        r = client.get("/api/genres/acidhouse")
        assert r.status_code == 200
        data = r.json()
        assert data["slug"] == "acidhouse"
        assert "tracks" in data
        assert isinstance(data["tracks"], list)

    def test_invalid_slug_404(self, client):
        r = client.get("/api/genres/nonexistent-slug-xyz")
        assert r.status_code == 404

    def test_genre_with_tracks(self, client):
        r = client.get("/api/genres/acidhouse")
        data = r.json()
        assert len(data["tracks"]) > 0


# ============================================================================
# 4. GET /api/search?q=techno
# ============================================================================


class TestSearch:
    def test_search_techno(self, client):
        r = client.get("/api/search", params={"q": "techno"})
        assert r.status_code == 200
        data = r.json()
        assert "query" in data
        assert data["query"] == "techno"
        assert "count" in data
        assert "genres" in data
        assert data["count"] > 0

    def test_search_no_query_400(self, client):
        r = client.get("/api/search")
        assert r.status_code in (400, 422)

    def test_search_empty_query_422(self, client):
        r = client.get("/api/search", params={"q": ""})
        assert r.status_code in (400, 422)

    def test_search_case_insensitive(self, client):
        r1 = client.get("/api/search", params={"q": "Techno"})
        r2 = client.get("/api/search", params={"q": "techno"})
        assert r1.json()["count"] == r2.json()["count"]


# ============================================================================
# 5. GET /api/stats
# ============================================================================


class TestStats:
    def test_stats_response(self, client):
        r = client.get("/api/stats")
        assert r.status_code == 200
        data = r.json()
        assert "sceneCount" in data
        assert "biomeCount" in data
        assert "scenes" in data
        assert "biomes" in data
        assert isinstance(data["scenes"], list)
        assert isinstance(data["biomes"], list)
        assert data["sceneCount"] > 0
        assert data["biomeCount"] > 0


# ============================================================================
# 6. GET /api/releases — filters and pagination
# ============================================================================


class TestReleases:
    def test_releases_default(self, client):
        r = client.get("/api/releases")
        assert r.status_code == 200
        data = r.json()
        assert "releases" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 20
        assert data["offset"] == 0

    def test_releases_filter_country(self, client):
        r = client.get("/api/releases", params={"country": "Germany"})
        assert r.status_code == 200
        data = r.json()
        for rel in data["releases"]:
            assert rel["country"] == "Germany"

    def test_releases_filter_year_range(self, client):
        r = client.get("/api/releases", params={"year_min": 2000, "year_max": 2005})
        assert r.status_code == 200
        data = r.json()
        for rel in data["releases"]:
            assert 2000 <= rel["year"] <= 2005

    def test_releases_filter_label(self, client):
        r = client.get("/api/releases", params={"label": "Svek"})
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1

    def test_releases_filter_q(self, client):
        r = client.get("/api/releases", params={"q": "Wink"})
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1

    def test_releases_pagination(self, client):
        r1 = client.get("/api/releases", params={"limit": 5, "offset": 0})
        r2 = client.get("/api/releases", params={"limit": 5, "offset": 5})
        assert r1.status_code == 200
        assert r2.status_code == 200
        ids1 = {rel["id"] for rel in r1.json()["releases"]}
        ids2 = {rel["id"] for rel in r2.json()["releases"]}
        assert ids1.isdisjoint(ids2), "Pages should not overlap"

    def test_releases_limit_cap(self, client):
        r = client.get("/api/releases", params={"limit": 200})
        assert r.status_code == 422  # exceeds le=100


# ============================================================================
# 7. GET /api/recommendations/{release_id}
# ============================================================================


class TestRecommendations:
    def test_recommendations_valid(self, client):
        r = client.get("/api/recommendations/1")
        assert r.status_code == 200
        data = r.json()
        assert "release" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    def test_recommendations_not_found(self, client):
        r = client.get("/api/recommendations/999999999")
        assert r.status_code == 404


# ============================================================================
# 8. GET /api/search/unified?q=house
# ============================================================================


class TestUnifiedSearch:
    def test_unified_search_house(self, client):
        r = client.get("/api/search/unified", params={"q": "house"})
        assert r.status_code == 200
        data = r.json()
        assert "query" in data
        assert "genres" in data
        assert "artists" in data
        assert "labels" in data
        assert isinstance(data["genres"], list)
        assert isinstance(data["artists"], list)
        assert isinstance(data["labels"], list)

    def test_unified_search_no_query(self, client):
        r = client.get("/api/search/unified")
        assert r.status_code in (400, 422)

    def test_unified_search_genre_has_score(self, client):
        r = client.get("/api/search/unified", params={"q": "techno"})
        data = r.json()
        if data["genres"]:
            assert "score" in data["genres"][0]
            assert "slug" in data["genres"][0]


# ============================================================================
# 9. GET /api/artists/{name}/releases
# ============================================================================


class TestArtists:
    def test_artist_releases(self, client):
        r = client.get("/api/artists/The Persuader/releases")
        assert r.status_code == 200
        data = r.json()
        assert "artist" in data
        assert "releases" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_artist_releases_unknown(self, client):
        r = client.get("/api/artists/ZZZZNONEXISTENT99999/releases")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["releases"] == []


# ============================================================================
# 10. GET /api/artists/{name}/timeline
# ============================================================================


class TestArtistTimeline:
    def test_artist_timeline(self, client):
        r = client.get("/api/artists/The Persuader/timeline")
        assert r.status_code == 200
        data = r.json()
        assert "artist" in data
        assert "timeline" in data
        assert "total" in data
        assert isinstance(data["timeline"], list)

    def test_artist_timeline_structure(self, client):
        r = client.get("/api/artists/The Persuader/timeline")
        data = r.json()
        if data["timeline"]:
            entry = data["timeline"][0]
            assert "title" in entry
            assert "year" in entry


# ============================================================================
# 11. GET /api/labels/{name}/releases
# ============================================================================


class TestLabels:
    def test_label_releases(self, client):
        r = client.get("/api/labels/Svek/releases")
        assert r.status_code == 200
        data = r.json()
        assert "label" in data
        assert "releases" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_label_releases_unknown(self, client):
        r = client.get("/api/labels/ZZZZNONEXISTENT99999/releases")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0


# ============================================================================
# 12. GET /api/labels/{name}/genres
# ============================================================================


class TestLabelGenres:
    def test_label_genres(self, client):
        r = client.get("/api/labels/Svek/genres")
        assert r.status_code == 200
        data = r.json()
        assert "label" in data
        assert "genres" in data
        assert isinstance(data["genres"], list)
        assert "release_count" in data


# ============================================================================
# 13. GET /api/cities
# ============================================================================


class TestCities:
    def test_list_cities(self, client):
        r = client.get("/api/cities")
        assert r.status_code == 200
        data = r.json()
        assert "cities" in data
        assert "count" in data
        assert data["count"] == 35

    def test_cities_filter_country(self, client):
        r = client.get("/api/cities", params={"country": "DE"})
        assert r.status_code == 200
        data = r.json()
        for city in data["cities"]:
            assert city["country"].upper() == "DE"

    def test_cities_city_structure(self, client):
        r = client.get("/api/cities")
        data = r.json()
        city = data["cities"][0]
        for key in ("id", "name", "country", "lat", "lng", "genres"):
            assert key in city, f"Missing key: {key}"


# ============================================================================
# 14. GET /api/cities/{city_id}
# ============================================================================


class TestCityById:
    def test_valid_city(self, client):
        r = client.get("/api/cities/detroit")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "detroit"
        assert data["name"] == "Detroit"

    def test_invalid_city_404(self, client):
        r = client.get("/api/cities/nonexistent-city-xyz")
        assert r.status_code == 404


# ============================================================================
# 15. GET /api/cities/{city_id}/artists
# ============================================================================


class TestCityArtists:
    def test_city_artists(self, client):
        r = client.get("/api/cities/detroit/artists")
        assert r.status_code == 200
        data = r.json()
        assert "city_id" in data
        assert "city_name" in data
        assert "artists" in data
        assert isinstance(data["artists"], list)

    def test_city_artists_invalid_city(self, client):
        r = client.get("/api/cities/nonexistent-city-xyz/artists")
        assert r.status_code == 404


# ============================================================================
# 16. GET /api/cities/{city_id}/labels
# ============================================================================


class TestCityLabels:
    def test_city_labels(self, client):
        r = client.get("/api/cities/detroit/labels")
        assert r.status_code == 200
        data = r.json()
        assert "city_id" in data
        assert "city_name" in data
        assert "labels" in data
        assert isinstance(data["labels"], list)

    def test_city_labels_invalid_city(self, client):
        r = client.get("/api/cities/nonexistent-city-xyz/labels")
        assert r.status_code == 404


# ============================================================================
# 17. GET /api/shops
# ============================================================================


class TestShops:
    def test_list_shops(self, client):
        r = client.get("/api/shops")
        assert r.status_code == 200
        data = r.json()
        assert "shops" in data
        assert "total" in data
        assert "count" in data
        assert data["total"] > 0

    def test_shops_filter_city(self, client):
        r = client.get("/api/shops", params={"city": "berlin"})
        assert r.status_code == 200
        data = r.json()
        for shop in data["shops"]:
            assert "berlin" in shop.get("city", "").lower()

    def test_shops_geo_search(self, client):
        r = client.get("/api/shops", params={"lat": 52.5, "lng": 13.4, "radius": 10})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["shops"], list)
        # All returned shops should be within ~10km of Berlin center
        assert data["count"] <= data["total"]


# ============================================================================
# 18. GET /api/auth/me — unauthenticated
# ============================================================================


class TestAuthMe:
    def test_me_unauthenticated(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert data["authenticated"] is False
        assert data["user"] is None

    def test_me_invalid_token(self, client):
        r = client.get("/api/auth/me", params={"session_token": "bogus-token"})
        assert r.status_code == 200
        data = r.json()
        assert data["authenticated"] is False


# ============================================================================
# 19. POST /api/paths — create dig path
# ============================================================================


class TestPaths:
    def test_create_path(self, client):
        payload = {
            "title": "Test Journey",
            "description": "A test dig path",
            "waypoints": [
                {"slug": "acidhouse", "note": "Start here"},
                {"slug": "techno", "note": "Then here"},
            ],
        }
        r = client.post("/api/paths", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["title"] == "Test Journey"
        assert len(data["waypoints"]) == 2
        assert data["views"] == 0

    def test_create_path_empty_waypoints_422(self, client):
        payload = {"title": "Bad", "waypoints": []}
        r = client.post("/api/paths", json=payload)
        assert r.status_code == 422

    def test_create_path_no_body_422(self, client):
        r = client.post("/api/paths")
        assert r.status_code == 422


# ============================================================================
# 20. GET /api/paths/popular
# ============================================================================


class TestPathsPopular:
    def test_popular_paths(self, client):
        # Create a path first so popular is not empty
        client.post("/api/paths", json={
            "title": "Popular test",
            "waypoints": [{"slug": "house"}],
        })
        r = client.get("/api/paths/popular")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1


# ============================================================================
# 21. GET /api/paths/{id}
# ============================================================================


class TestPathById:
    def test_get_path_increments_views(self, client):
        # Create a path
        cr = client.post("/api/paths", json={
            "title": "View test",
            "waypoints": [{"slug": "deephouse"}],
        })
        path_id = cr.json()["id"]

        r1 = client.get(f"/api/paths/{path_id}")
        assert r1.status_code == 200
        assert r1.json()["views"] == 1

        r2 = client.get(f"/api/paths/{path_id}")
        assert r2.json()["views"] == 2

    def test_get_path_not_found(self, client):
        r = client.get("/api/paths/nonexistent-id-xyz")
        assert r.status_code == 404


# ============================================================================
# 22. GET /api/taste-profile
# ============================================================================


class TestTasteProfile:
    def test_taste_profile_requires_username(self, client):
        r = client.get("/api/taste-profile")
        assert r.status_code == 422

    def test_taste_profile_unknown_user(self, client):
        r = client.get("/api/taste-profile", params={"discogs_username": "zzzz_nonexistent_user_999"})
        # Should be 400 (not synced) since user doesn't exist in our user_db
        assert r.status_code == 400


# ============================================================================
# 23. GET /api/recommendations/personal
# ============================================================================


class TestPersonalRecommendations:
    def test_personal_requires_username(self, client):
        r = client.get("/api/recommendations/personal")
        assert r.status_code == 422


# ============================================================================
# 24. GET /api/crate-neighbors/{id}
# ============================================================================


class TestCrateNeighbors:
    def test_crate_neighbors(self, client):
        r = client.get("/api/crate-neighbors/1")
        # Either 200 (data available) or 503 (CF DB not built)
        assert r.status_code in (200, 503)
        if r.status_code == 200:
            data = r.json()
            assert "release_id" in data
            assert "crate_neighbors" in data
        else:
            assert "not available" in r.json()["detail"].lower()


# ============================================================================
# 25. GET /api/collection — requires session
# ============================================================================


class TestCollection:
    def test_collection_no_session_401(self, client):
        r = client.get("/api/collection")
        # session_token is required query param; missing = 422, invalid = 401
        assert r.status_code == 422

    def test_collection_invalid_session_401(self, client):
        r = client.get("/api/collection", params={"session_token": "bogus"})
        assert r.status_code == 401
