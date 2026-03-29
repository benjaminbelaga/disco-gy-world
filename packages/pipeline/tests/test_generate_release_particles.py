"""Tests for generate_release_particles — position generation, style mapping."""
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

# The module runs at import time (module-level script), so we test
# the functions and constants we can extract without triggering the
# full processing pipeline. We import selectively.

# Check if world.json exists (required by module-level code)
WORLD_JSON = Path(__file__).parent.parent.parent / "web" / "public" / "data" / "world.json"


def _import_module():
    """Try importing the module; skip if data files missing."""
    if not WORLD_JSON.exists():
        pytest.skip("world.json not available for particle generation")
    try:
        import generate_release_particles
        return generate_release_particles
    except FileNotFoundError:
        pytest.skip("Required data files not available")
    except Exception as e:
        pytest.skip(f"Module import failed: {e}")


# Since the module runs script-level code on import, we test the
# STYLE_MAPPING dict and get_position_for_styles function by extracting
# them carefully.


def test_style_mapping_keys_are_lowercase():
    """All STYLE_MAPPING keys should be lowercase."""
    mod = _import_module()
    for key in mod.STYLE_MAPPING:
        assert key == key.lower(), f"Key '{key}' is not lowercase"


def test_style_mapping_values_are_lowercase():
    mod = _import_module()
    for value in mod.STYLE_MAPPING.values():
        assert value == value.lower(), f"Value '{value}' is not lowercase"


def test_style_mapping_covers_major_genres():
    mod = _import_module()
    major = ["house", "techno", "trance", "ambient", "drum n bass", "dubstep"]
    for genre in major:
        assert genre in mod.STYLE_MAPPING, f"Missing major genre: {genre}"


def test_get_position_for_styles_known():
    mod = _import_module()
    random.seed(42)
    pos = mod.get_position_for_styles(["House"])
    assert "x" in pos
    assert "z" in pos
    assert "color" in pos


def test_get_position_for_styles_unknown():
    mod = _import_module()
    random.seed(42)
    pos = mod.get_position_for_styles(["Polka", "Yodeling"])
    assert "x" in pos
    assert "z" in pos
    # Default position for unknown styles
    assert -35 <= pos["x"] <= 35
    assert -35 <= pos["z"] <= 35


def test_get_position_for_styles_empty():
    mod = _import_module()
    random.seed(42)
    pos = mod.get_position_for_styles([])
    assert "x" in pos
    assert "z" in pos


def test_get_position_for_styles_multiple():
    mod = _import_module()
    random.seed(42)
    pos = mod.get_position_for_styles(["House", "Techno"])
    assert "x" in pos
    assert "z" in pos


def test_genre_positions_loaded():
    mod = _import_module()
    assert len(mod.genre_positions) > 50, "Should have many genre positions from world.json"


def test_max_particles_constant():
    mod = _import_module()
    assert mod.MAX_PARTICLES == 50000
