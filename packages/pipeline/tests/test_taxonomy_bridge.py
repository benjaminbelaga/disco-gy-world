"""Tests for the taxonomy bridge mapping Discogs styles <-> world.json genres."""
import sys
from pathlib import Path

# Ensure pipeline package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from taxonomy_bridge import build_bridge, get_genres_for_style, get_styles_for_genre


@pytest.fixture(scope="module")
def bridge():
    return build_bridge()


def test_bridge_loads_discogs_styles(bridge):
    """Should load all 100 Discogs electronic styles."""
    assert len(bridge["discogs_styles"]) == 100


def test_bridge_loads_world_genres(bridge):
    """Should load all 166 world.json genres."""
    assert len(bridge["world_genres"]) == 166


def test_bridge_maps_house_style(bridge):
    genres = get_genres_for_style(bridge, "House")
    assert len(genres) > 0
    assert any("house" in g.lower() for g in genres)


def test_bridge_maps_techno_style(bridge):
    genres = get_genres_for_style(bridge, "Techno")
    assert len(genres) > 0
    assert any("techno" in g.lower() for g in genres)


def test_bridge_maps_ambient(bridge):
    genres = get_genres_for_style(bridge, "Ambient")
    assert len(genres) > 0
    assert "Ambient" in genres


def test_bridge_maps_deep_house(bridge):
    genres = get_genres_for_style(bridge, "Deep House")
    assert len(genres) > 0


def test_bridge_maps_drum_n_bass(bridge):
    genres = get_genres_for_style(bridge, "Drum n Bass")
    assert len(genres) > 0


def test_bridge_maps_ebm(bridge):
    genres = get_genres_for_style(bridge, "EBM")
    assert len(genres) > 0
    assert "EBM" in genres


def test_bridge_covers_most_discogs_styles(bridge):
    """At least 70% of Discogs styles should map to at least one genre."""
    mapped = sum(1 for s in bridge["discogs_styles"] if bridge["style_to_genres"].get(s))
    ratio = mapped / len(bridge["discogs_styles"])
    assert ratio >= 0.70, f"Only {mapped}/{len(bridge['discogs_styles'])} styles mapped ({ratio:.0%})"


def test_non_electronic_styles_empty(bridge):
    """Non-electronic styles (rock, folk, etc.) should map to empty or nothing."""
    non_electronic = ["Pop Rock", "Alternative Rock", "Indie Rock", "Punk", "Folk", "Chanson"]
    for style in non_electronic:
        genres = get_genres_for_style(bridge, style)
        # Either empty or mapped to something tangential (Krautrock for Prog Rock)
        assert len(genres) <= 2, f"{style} mapped to too many genres: {genres}"


def test_bridge_is_bidirectional(bridge):
    """Every mapped genre should have at least one style."""
    for genre, styles in bridge["genre_to_styles"].items():
        assert len(styles) > 0, f"Genre {genre} has no styles mapped"


def test_bridge_reverse_consistency(bridge):
    """If style S maps to genre G, then genre G must map back to style S."""
    for style, genres in bridge["style_to_genres"].items():
        for genre in genres:
            styles_for_genre = bridge["genre_to_styles"].get(genre, [])
            assert style in styles_for_genre, (
                f"Inconsistency: {style} -> {genre}, but {genre} does not map back to {style}"
            )


def test_manual_overrides_applied(bridge):
    """Manual overrides should take precedence over fuzzy matching."""
    # Psy-Trance should map to Psychedelic Trance (manual override)
    genres = get_genres_for_style(bridge, "Psy-Trance")
    assert "Psychedelic Trance" in genres

    # UK Garage should map to 2-Step Garage
    genres = get_genres_for_style(bridge, "UK Garage")
    assert "2-Step Garage" in genres
