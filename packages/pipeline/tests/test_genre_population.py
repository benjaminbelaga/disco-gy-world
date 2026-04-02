"""Tests for genre_population — release counting per genre via taxonomy bridge."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from genre_population import (
    count_releases_per_genre,
    enrich_world_json,
    print_top_genres,
    JSONL_PATH,
    WORLD_JSON_PATH,
)


# --- count_releases_per_genre ---

def test_count_releases_requires_jsonl():
    """Should fail gracefully or skip if JSONL data not available."""
    if not JSONL_PATH.exists():
        pytest.skip("electronic_releases.jsonl not available")
    counts = count_releases_per_genre(limit=100)
    assert isinstance(counts, dict)


def test_count_releases_returns_dict():
    if not JSONL_PATH.exists():
        pytest.skip("electronic_releases.jsonl not available")
    counts = count_releases_per_genre(limit=50)
    assert isinstance(counts, dict)
    for genre, count in counts.items():
        assert isinstance(genre, str)
        assert isinstance(count, int)
        assert count > 0


def test_count_releases_with_limit():
    if not JSONL_PATH.exists():
        pytest.skip("electronic_releases.jsonl not available")
    counts_small = count_releases_per_genre(limit=10)
    counts_larger = count_releases_per_genre(limit=100)
    # Larger limit should produce >= as many total mappings
    total_small = sum(counts_small.values())
    total_larger = sum(counts_larger.values())
    assert total_larger >= total_small


# --- enrich_world_json ---

def test_enrich_world_json_updates_counts(tmp_path):
    """Test enrichment with a synthetic world.json."""
    world = {
        "genres": [
            {"name": "Techno", "slug": "techno"},
            {"name": "House", "slug": "house"},
            {"name": "Ambient", "slug": "ambient"},
        ],
        "links": [],
    }
    world_path = tmp_path / "world.json"
    with open(world_path, "w") as f:
        json.dump(world, f)

    genre_counts = {"Techno": 5000, "House": 3000}

    # Temporarily patch the module's path
    import genre_population
    original_path = genre_population.WORLD_JSON_PATH
    genre_population.WORLD_JSON_PATH = world_path

    try:
        enrich_world_json(genre_counts)
        with open(world_path) as f:
            enriched = json.load(f)
        assert enriched["genres"][0]["release_count"] == 5000
        assert enriched["genres"][1]["release_count"] == 3000
        assert enriched["genres"][2]["release_count"] == 0
    finally:
        genre_population.WORLD_JSON_PATH = original_path


# --- print_top_genres ---

def test_print_top_genres_no_crash(capsys):
    """print_top_genres should not crash with valid or empty data."""
    print_top_genres({"Techno": 100, "House": 50}, n=5)
    captured = capsys.readouterr()
    assert "Techno" in captured.out


def test_print_top_genres_empty(capsys):
    print_top_genres({}, n=5)
    captured = capsys.readouterr()
    assert "Top" in captured.out


# --- Path constants ---

def test_jsonl_path_is_valid():
    """JSONL path should point to a reasonable location."""
    assert "electronic_releases.jsonl" in str(JSONL_PATH)


def test_world_json_path_is_valid():
    assert "world.json" in str(WORLD_JSON_PATH)
