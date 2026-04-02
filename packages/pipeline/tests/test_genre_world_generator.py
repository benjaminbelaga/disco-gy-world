"""Tests for genre_world_generator — Voronoi layout, biome elevation, territory building."""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

try:
    import numpy as np
    from genre_world_generator import (
        build_adjacency,
        compute_elevation,
        compute_voronoi,
        force_directed_refine,
        _hexagon,
        _polygon_area,
        _clip_to_circle,
        BIOME_ELEVATION,
        WORLD_RADIUS,
    )
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

pytestmark = pytest.mark.skipif(not HAS_NUMPY, reason="numpy/scipy not available")


# --- Fixtures ---

def _make_genres(n=5):
    """Create synthetic genre data with positions."""
    genres = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        genres.append({
            "name": f"Genre{i}",
            "slug": f"genre-{i}",
            "scene": f"Scene{i % 2}",
            "biome": "techno-massif" if i % 2 == 0 else "house-plains",
            "x": 10 * math.cos(angle),
            "z": 10 * math.sin(angle),
            "color": "#ffffff",
            "release_count": (i + 1) * 100,
        })
    return genres


def _make_links(genres):
    """Create circular links between genres."""
    links = []
    for i in range(len(genres)):
        links.append({
            "source": genres[i]["slug"],
            "target": genres[(i + 1) % len(genres)]["slug"],
        })
    return links


# --- build_adjacency ---

def test_build_adjacency_returns_dict():
    genres = _make_genres(3)
    links = _make_links(genres)
    adj = build_adjacency(genres, links)
    assert isinstance(adj, dict)


def test_build_adjacency_bidirectional():
    genres = _make_genres(3)
    links = [{"source": "genre-0", "target": "genre-1"}]
    adj = build_adjacency(genres, links)
    assert any(t == "genre-1" for t, _ in adj["genre-0"])
    assert any(t == "genre-0" for t, _ in adj["genre-1"])


def test_build_adjacency_ignores_unknown_slugs():
    genres = _make_genres(2)
    links = [{"source": "genre-0", "target": "nonexistent"}]
    adj = build_adjacency(genres, links)
    assert len(adj.get("genre-0", [])) == 0


def test_build_adjacency_empty_links():
    genres = _make_genres(3)
    adj = build_adjacency(genres, [])
    assert all(len(v) == 0 for v in adj.values())


def test_build_adjacency_weighted_links():
    genres = _make_genres(2)
    links = [{"source": "genre-0", "target": "genre-1", "startYear": 1990, "endYear": 2000}]
    adj = build_adjacency(genres, links)
    _, weight = adj["genre-0"][0]
    assert weight == pytest.approx(0.1, abs=0.01)


# --- compute_elevation ---

def test_elevation_techno_massif_high():
    genre = {"biome": "techno-massif", "scene": "Techno", "release_count": 1000}
    elev = compute_elevation(genre)
    assert elev > 0.7


def test_elevation_ambient_low():
    genre = {"biome": "ambient-depths", "scene": "Ambient", "release_count": 100}
    elev = compute_elevation(genre)
    assert elev < 0.4


def test_elevation_clamped_to_range():
    # Extreme values should still be within [0.05, 1.0]
    genre_high = {"biome": "techno-massif", "scene": "Hardcore", "release_count": 10_000_000}
    genre_low = {"biome": "ambient-depths", "scene": "Ambient", "release_count": 0}
    assert 0.05 <= compute_elevation(genre_high) <= 1.0
    assert 0.05 <= compute_elevation(genre_low) <= 1.0


def test_elevation_unknown_biome_defaults():
    genre = {"biome": "nonexistent", "scene": "Unknown", "release_count": 0}
    elev = compute_elevation(genre)
    assert elev == pytest.approx(0.30, abs=0.1)


def test_elevation_zero_release_count():
    genre = {"biome": "house-plains", "scene": "House", "release_count": 0}
    elev = compute_elevation(genre)
    assert 0.05 <= elev <= 1.0


# --- _hexagon ---

def test_hexagon_has_6_vertices():
    center = np.array([0.0, 0.0])
    hex_verts = _hexagon(center, 5.0)
    assert hex_verts.shape == (6, 2)


def test_hexagon_radius():
    center = np.array([10.0, 20.0])
    hex_verts = _hexagon(center, 5.0)
    distances = np.linalg.norm(hex_verts - center, axis=1)
    np.testing.assert_allclose(distances, 5.0, atol=1e-10)


# --- _polygon_area ---

def test_polygon_area_unit_square():
    square = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
    assert _polygon_area(square) == pytest.approx(1.0)


def test_polygon_area_triangle():
    triangle = np.array([[0, 0], [4, 0], [0, 3]])
    assert _polygon_area(triangle) == pytest.approx(6.0)


def test_polygon_area_empty():
    assert _polygon_area(np.array([])) == 0.0


def test_polygon_area_two_points():
    assert _polygon_area(np.array([[0, 0], [1, 1]])) == 0.0


# --- _clip_to_circle ---

def test_clip_to_circle_all_inside():
    verts = np.array([[1, 0], [0, 1], [-1, 0], [0, -1]], dtype=float)
    clipped = _clip_to_circle(verts, 10.0)
    assert len(clipped) == 4


def test_clip_to_circle_partially_outside():
    verts = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=float)
    clipped = _clip_to_circle(verts, 5.0)
    # Should have fewer or different vertices due to clipping
    assert len(clipped) >= 2


# --- compute_voronoi ---

def test_compute_voronoi_returns_correct_count():
    genres = _make_genres(5)
    _, polygons = compute_voronoi(genres)
    assert len(polygons) == 5


def test_compute_voronoi_polygons_have_vertices():
    genres = _make_genres(5)
    _, polygons = compute_voronoi(genres)
    for poly in polygons:
        assert len(poly) >= 3, "Each polygon should have at least 3 vertices"


# --- force_directed_refine ---

def test_force_directed_refine_preserves_count():
    genres = _make_genres(5)
    adj = build_adjacency(genres, _make_links(genres))
    refined = force_directed_refine(genres, adj)
    assert len(refined) == 5


def test_force_directed_refine_stays_in_bounds():
    genres = _make_genres(5)
    adj = build_adjacency(genres, _make_links(genres))
    refined = force_directed_refine(genres, adj)
    for g in refined:
        dist = math.sqrt(g["x"] ** 2 + g["z"] ** 2)
        assert dist <= WORLD_RADIUS + 0.1, f"Genre {g['slug']} at distance {dist} exceeds world radius"


def test_force_directed_refine_preserves_fields():
    genres = _make_genres(3)
    adj = build_adjacency(genres, [])
    refined = force_directed_refine(genres, adj)
    for g in refined:
        assert "name" in g
        assert "slug" in g
        assert "scene" in g


# --- BIOME_ELEVATION constants ---

def test_biome_elevation_values_in_range():
    for biome, elev in BIOME_ELEVATION.items():
        assert 0.0 <= elev <= 1.0, f"Biome {biome} elevation {elev} out of range"
