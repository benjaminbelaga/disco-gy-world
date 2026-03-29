"""Tests for style co-occurrence matrix builder."""
import sys
from pathlib import Path

# Allow imports from parent package
sys.path.insert(0, str(Path(__file__).parent.parent))

from style_cooccurrence import build_cooccurrence


def test_cooccurrence_returns_pairs():
    """Releases with shared styles produce co-occurrence pairs."""
    test_releases = [
        {"styles": ["House", "Deep House"]},
        {"styles": ["House", "Acid House"]},
        {"styles": ["Techno", "Acid"]},
        {"styles": ["House", "Deep House", "Acid House"]},
    ]
    matrix = build_cooccurrence(test_releases)
    assert ("Deep House", "House") in matrix or ("House", "Deep House") in matrix


def test_cooccurrence_counts_are_correct():
    """Pair counts accumulate correctly across releases."""
    test_releases = [
        {"styles": ["House", "Deep House"]},
        {"styles": ["House", "Deep House"]},
        {"styles": ["Techno"]},
    ]
    matrix = build_cooccurrence(test_releases)
    pair = tuple(sorted(["House", "Deep House"]))
    assert matrix[pair] == 2


def test_single_style_releases_excluded():
    """Releases with only one style produce no pairs."""
    test_releases = [{"styles": ["Techno"]}]
    matrix = build_cooccurrence(test_releases)
    assert len(matrix) == 0


def test_empty_styles_excluded():
    """Releases with empty or missing styles produce no pairs."""
    test_releases = [
        {"styles": []},
        {"styles": None},
        {},
    ]
    matrix = build_cooccurrence(test_releases)
    assert len(matrix) == 0


def test_three_styles_produce_three_pairs():
    """A release with 3 styles produces C(3,2) = 3 pairs."""
    test_releases = [{"styles": ["A", "B", "C"]}]
    matrix = build_cooccurrence(test_releases)
    assert len(matrix) == 3
    assert matrix[("A", "B")] == 1
    assert matrix[("A", "C")] == 1
    assert matrix[("B", "C")] == 1


def test_duplicate_styles_in_release_deduplicated():
    """Duplicate styles within a single release are deduplicated."""
    test_releases = [{"styles": ["House", "House", "Techno"]}]
    matrix = build_cooccurrence(test_releases)
    assert len(matrix) == 1
    pair = tuple(sorted(["House", "Techno"]))
    assert matrix[pair] == 1


def test_smoke_first_10k_releases():
    """Smoke test: run on first 10K real releases if available."""
    from itertools import islice

    try:
        from style_cooccurrence import stream_releases
        releases = list(islice(stream_releases(), 10_000))
    except FileNotFoundError:
        import pytest
        pytest.skip("JSONL data file not available")

    matrix = build_cooccurrence(releases)
    assert len(matrix) > 0, "Expected at least some co-occurrence pairs in 10K releases"

    # Top pairs should have reasonable counts
    top = sorted(matrix.items(), key=lambda x: -x[1])[:10]
    for pair, count in top:
        assert count > 0
        assert len(pair) == 2
        assert pair[0] < pair[1], "Pairs should be sorted alphabetically"
