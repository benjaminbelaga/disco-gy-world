"""
Genre Population: Count Discogs releases per world.json genre.

Streams the electronic_releases.jsonl, maps each release's styles
to world.json genres via the taxonomy bridge, and counts.
Can enrich world.json with release_count per genre.
"""
import json
import sys
from collections import Counter
from pathlib import Path

# Ensure sibling imports work
sys.path.insert(0, str(Path(__file__).parent))

from taxonomy_bridge import build_bridge, get_genres_for_style

PROJECT_ROOT = Path(__file__).parent.parent.parent
JSONL_PATH = PROJECT_ROOT / "data" / "processed" / "electronic_releases.jsonl"
WORLD_JSON_PATH = PROJECT_ROOT / "packages" / "web" / "public" / "data" / "world.json"


def count_releases_per_genre(limit: int | None = None) -> dict[str, int]:
    """Stream JSONL and count releases per world.json genre.

    Args:
        limit: If set, only process this many releases (for testing).

    Returns:
        Dict of genre_name -> release_count.
    """
    bridge = build_bridge()
    genre_counts: Counter = Counter()
    processed = 0
    mapped = 0

    with open(JSONL_PATH) as f:
        for line in f:
            if limit and processed >= limit:
                break
            processed += 1

            try:
                release = json.loads(line)
            except json.JSONDecodeError:
                continue

            styles = release.get("styles", [])
            if not styles:
                continue

            # Collect all genres for this release (deduplicated)
            release_genres: set[str] = set()
            for style in styles:
                genres = get_genres_for_style(bridge, style)
                release_genres.update(genres)

            if release_genres:
                mapped += 1
                for genre in release_genres:
                    genre_counts[genre] += 1

            if processed % 500_000 == 0:
                print(f"  ...processed {processed:,} releases ({mapped:,} mapped)")

    print(f"Done: {processed:,} releases processed, {mapped:,} mapped to genres")
    return dict(genre_counts)


def enrich_world_json(genre_counts: dict[str, int]) -> None:
    """Add release_count to each genre in world.json."""
    with open(WORLD_JSON_PATH) as f:
        world = json.load(f)

    enriched = 0
    for genre in world["genres"]:
        name = genre["name"]
        count = genre_counts.get(name, 0)
        genre["release_count"] = count
        if count > 0:
            enriched += 1

    with open(WORLD_JSON_PATH, "w") as f:
        json.dump(world, f, indent=2)

    total = len(world["genres"])
    print(f"Enriched world.json: {enriched}/{total} genres have release counts")


def print_top_genres(genre_counts: dict[str, int], n: int = 20) -> None:
    """Print top N genres by release count."""
    top = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:n]
    print(f"\nTop {n} genres by release count:")
    print("-" * 45)
    for i, (genre, count) in enumerate(top, 1):
        print(f"  {i:2d}. {genre:<30s} {count:>8,}")
    print(f"\nTotal unique genres with releases: {sum(1 for c in genre_counts.values() if c > 0)}")
    print(f"Total genre-release mappings: {sum(genre_counts.values()):,}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Count releases per genre")
    parser.add_argument("--limit", type=int, help="Limit releases to process (for testing)")
    parser.add_argument("--enrich", action="store_true", help="Write release_count to world.json")
    args = parser.parse_args()

    counts = count_releases_per_genre(limit=args.limit)
    print_top_genres(counts)

    if args.enrich:
        enrich_world_json(counts)
