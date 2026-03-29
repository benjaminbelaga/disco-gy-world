"""Tests for heightmap_generator — point-in-polygon, territory lookup, elevation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

try:
    import numpy as np
    from heightmap_generator import (
        point_in_polygon,
        build_territory_lookup,
        OCEAN_LEVEL,
        HEIGHTMAP_SIZE,
    )
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

pytestmark = pytest.mark.skipif(not HAS_NUMPY, reason="numpy/scipy not available")


# --- point_in_polygon ---

def test_point_inside_square():
    square = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=float)
    assert point_in_polygon(np.array([5.0, 5.0]), square) is True


def test_point_outside_square():
    square = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=float)
    assert point_in_polygon(np.array([15.0, 5.0]), square) is False


def test_point_inside_triangle():
    tri = np.array([[0, 0], [10, 0], [5, 10]], dtype=float)
    assert point_in_polygon(np.array([5.0, 3.0]), tri) is True


def test_point_outside_triangle():
    tri = np.array([[0, 0], [10, 0], [5, 10]], dtype=float)
    assert point_in_polygon(np.array([0.0, 10.0]), tri) is False


def test_point_at_origin_inside_centered_square():
    square = np.array([[-5, -5], [5, -5], [5, 5], [-5, 5]], dtype=float)
    assert point_in_polygon(np.array([0.0, 0.0]), square) is True


def test_point_far_away():
    square = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
    assert point_in_polygon(np.array([1000.0, 1000.0]), square) is False


# --- build_territory_lookup ---

def test_territory_lookup_small_grid():
    """Test territory lookup with a single large territory covering most of the grid."""
    territories = [{
        "polygon": [[-40, -40], [40, -40], [40, 40], [-40, 40]],
        "elevation": 0.5,
        "scene": "Test",
        "release_count": 100,
    }]
    size = 32  # Small for speed
    world_radius = 48.0
    grid = build_territory_lookup(territories, size, world_radius)
    assert grid.shape == (size, size)
    # Most inner pixels should be territory 0
    center_region = grid[8:24, 8:24]
    land_pixels = np.sum(center_region >= 0)
    assert land_pixels > 0, "Center should have land pixels"


def test_territory_lookup_empty_territories():
    """Empty territory list should produce all-ocean grid."""
    grid = build_territory_lookup([], 16, 48.0)
    assert np.all(grid == -1)


def test_territory_lookup_returns_correct_shape():
    territories = [{
        "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]],
        "elevation": 0.5,
        "scene": "Test",
        "release_count": 0,
    }]
    grid = build_territory_lookup(territories, 64, 48.0)
    assert grid.shape == (64, 64)
    assert grid.dtype == np.int32


# --- Constants ---

def test_ocean_level_in_range():
    assert 0.0 < OCEAN_LEVEL < 0.5


def test_heightmap_size_is_power_of_two():
    assert HEIGHTMAP_SIZE & (HEIGHTMAP_SIZE - 1) == 0, "HEIGHTMAP_SIZE should be power of 2"
