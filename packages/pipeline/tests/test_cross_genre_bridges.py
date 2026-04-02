"""Tests for cross_genre_bridges — style-to-cluster mapping, bridge detection logic."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from cross_genre_bridges import (
    get_release_clusters,
    STYLE_TO_CLUSTER,
)


# --- get_release_clusters ---

def test_get_release_clusters_json_string():
    styles_json = json.dumps(["Techno", "Acid"])
    clusters = get_release_clusters(styles_json)
    assert "Techno" in clusters


def test_get_release_clusters_multiple_clusters():
    styles_json = json.dumps(["Techno", "Deep House", "Ambient"])
    clusters = get_release_clusters(styles_json)
    assert clusters == {"Techno", "House", "Ambient"}


def test_get_release_clusters_single_cluster():
    styles_json = json.dumps(["Techno", "Minimal", "Acid"])
    clusters = get_release_clusters(styles_json)
    assert clusters == {"Techno"}


def test_get_release_clusters_empty_string():
    clusters = get_release_clusters("")
    assert clusters == set()


def test_get_release_clusters_none():
    clusters = get_release_clusters(None)
    assert clusters == set()


def test_get_release_clusters_unknown_styles():
    styles_json = json.dumps(["Polka", "Yodeling"])
    clusters = get_release_clusters(styles_json)
    assert clusters == set()


def test_get_release_clusters_comma_separated_fallback():
    """Non-JSON string should be parsed as comma-separated."""
    clusters = get_release_clusters("Techno, Deep House")
    assert "Techno" in clusters
    assert "House" in clusters


def test_get_release_clusters_invalid_json():
    clusters = get_release_clusters("{invalid json")
    assert isinstance(clusters, set)


# --- STYLE_TO_CLUSTER mapping ---

def test_style_to_cluster_has_techno():
    assert "Techno" in STYLE_TO_CLUSTER
    assert STYLE_TO_CLUSTER["Techno"] == "Techno"


def test_style_to_cluster_has_house():
    assert "House" in STYLE_TO_CLUSTER
    assert STYLE_TO_CLUSTER["House"] == "House"


def test_style_to_cluster_has_ambient():
    assert "Ambient" in STYLE_TO_CLUSTER
    assert STYLE_TO_CLUSTER["Ambient"] == "Ambient"


def test_style_to_cluster_has_dnb():
    assert "Drum n Bass" in STYLE_TO_CLUSTER
    assert STYLE_TO_CLUSTER["Drum n Bass"] == "DnB"


def test_all_clusters_are_strings():
    for style, cluster in STYLE_TO_CLUSTER.items():
        assert isinstance(style, str)
        assert isinstance(cluster, str)


def test_cluster_values_are_limited_set():
    """Clusters should be a small set of broad genre categories."""
    unique_clusters = set(STYLE_TO_CLUSTER.values())
    assert len(unique_clusters) <= 15, f"Too many clusters: {unique_clusters}"
    assert len(unique_clusters) >= 5, f"Too few clusters: {unique_clusters}"


def test_subgenres_map_to_parent_cluster():
    """Subgenres should map to same cluster as their parent."""
    assert STYLE_TO_CLUSTER.get("Minimal") == STYLE_TO_CLUSTER.get("Techno")
    assert STYLE_TO_CLUSTER.get("Deep House") == STYLE_TO_CLUSTER.get("House")
    assert STYLE_TO_CLUSTER.get("Goa Trance") == STYLE_TO_CLUSTER.get("Trance")


def test_find_bridge_releases_skipped_without_db():
    """find_bridge_releases requires databases — skip if not available."""
    from cross_genre_bridges import CF_DB_PATH, MAIN_DB_PATH
    if not CF_DB_PATH.exists() or not MAIN_DB_PATH.exists():
        pytest.skip("Full databases not available for bridge detection")
