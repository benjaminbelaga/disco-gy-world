"""Tests for content-based similarity index."""
import pytest
from similarity_index import build_feature_vectors, find_neighbors


def test_same_style_releases_are_similar():
    """Releases sharing styles + label should be top neighbors."""
    releases = [
        {"id": 1, "styles": ["Deep House", "House"], "label": "Trax", "year": 1990},
        {"id": 2, "styles": ["Deep House", "House"], "label": "Trax", "year": 1991},
        {"id": 3, "styles": ["Gabber", "Hardcore"], "label": "Mokum", "year": 1995},
    ]
    vectors = build_feature_vectors(releases)
    neighbors = find_neighbors(vectors, release_id=1, top_n=2)
    assert neighbors[0][0] == 2  # Release 2 most similar to 1


def test_different_styles_zero_similarity():
    """Releases with no shared styles/label should have zero similarity (filtered out)."""
    releases = [
        {"id": 1, "styles": ["Deep House"], "label": "A", "year": 1990},
        {"id": 2, "styles": ["Gabber"], "label": "B", "year": 1995},
    ]
    vectors = build_feature_vectors(releases)
    neighbors = find_neighbors(vectors, release_id=1, top_n=1)
    # No overlap at all — cosine similarity is 0, so no neighbors returned
    assert len(neighbors) == 0


def test_label_overlap_boosts_similarity():
    """Same label should boost similarity even with partial style overlap."""
    releases = [
        {"id": 1, "styles": ["Techno", "Minimal"], "label": "Kompakt", "year": 2005},
        {"id": 2, "styles": ["Techno"], "label": "Kompakt", "year": 2006},
        {"id": 3, "styles": ["Techno", "Minimal"], "label": "Tresor", "year": 2005},
    ]
    vectors = build_feature_vectors(releases)
    neighbors = find_neighbors(vectors, release_id=1, top_n=2)
    # Release 3 shares both styles; release 2 shares label + 1 style
    # Both should appear as neighbors
    neighbor_ids = [n[0] for n in neighbors]
    assert 2 in neighbor_ids
    assert 3 in neighbor_ids


def test_empty_release_list():
    """Empty input should produce empty vectors."""
    vectors = build_feature_vectors([])
    assert vectors["matrix"].shape[0] == 0


def test_find_neighbors_unknown_id():
    """Unknown release_id returns empty list."""
    releases = [
        {"id": 1, "styles": ["House"], "label": "A"},
    ]
    vectors = build_feature_vectors(releases)
    neighbors = find_neighbors(vectors, release_id=999, top_n=5)
    assert neighbors == []


def test_five_releases_ranking():
    """Verify correct ranking across 5 releases with known similarities."""
    releases = [
        {"id": 10, "styles": ["Dub Techno", "Ambient"], "label": "Basic Channel"},
        {"id": 20, "styles": ["Dub Techno", "Ambient"], "label": "Chain Reaction"},
        {"id": 30, "styles": ["Dub Techno"], "label": "Basic Channel"},
        {"id": 40, "styles": ["Ambient"], "label": "Basic Channel"},
        {"id": 50, "styles": ["Gabber", "Hardcore"], "label": "Mokum"},
    ]
    vectors = build_feature_vectors(releases)
    neighbors = find_neighbors(vectors, release_id=10, top_n=4)

    # Release 20 shares both styles (different label) — high
    # Release 30 shares 1 style + label — high
    # Release 40 shares 1 style + label — high
    # Release 50 shares nothing — zero similarity, filtered out
    neighbor_ids = [n[0] for n in neighbors]
    assert 50 not in neighbor_ids  # Zero overlap = not a neighbor
    assert len(neighbors) == 3  # Only 3 releases have any overlap
    assert neighbors[0][1] > neighbors[-1][1]  # Top > bottom
