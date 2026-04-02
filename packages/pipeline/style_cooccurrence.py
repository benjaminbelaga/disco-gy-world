"""
Build a style co-occurrence matrix from Discogs releases.
Counts how often two styles appear together on the same release.
This creates weighted edges between styles in the genre graph.
"""
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def build_cooccurrence(releases=None) -> dict[tuple, int]:
    """Build co-occurrence counts from an iterable of release dicts.

    Each release must have a "styles" list. Releases with fewer than 2
    styles are skipped. Pairs are stored as sorted tuples so
    ("A", "B") and ("B", "A") map to the same key.
    """
    if releases is None:
        releases = stream_releases()

    pair_counts: Counter = Counter()
    for release in releases:
        styles = release.get("styles") or []
        if len(styles) < 2:
            continue
        for pair in combinations(sorted(set(styles)), 2):
            pair_counts[pair] += 1

    return dict(pair_counts)


def stream_releases():
    """Stream releases line-by-line from the JSONL file (never loads all in memory)."""
    jsonl_path = DATA_DIR / "processed" / "electronic_releases.jsonl"
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Releases file not found: {jsonl_path}")
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def save_cooccurrence(output_path: Path | None = None, top_n: int = 1000):
    """Build and save top N co-occurrence pairs to JSON."""
    matrix = build_cooccurrence()
    sorted_pairs = sorted(matrix.items(), key=lambda x: -x[1])[:top_n]
    result = {f"{a}|{b}": count for (a, b), count in sorted_pairs}

    path = output_path or DATA_DIR / "style_cooccurrence.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Co-occurrence matrix saved: {len(result)} pairs")
    return result


if __name__ == "__main__":
    save_cooccurrence()
