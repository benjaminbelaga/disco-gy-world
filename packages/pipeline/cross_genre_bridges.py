"""
Find "gateway records" — releases owned by fans of 2+ different genres.

A bridge release appears in collections where the user's other releases
span different genre clusters. These releases connect genre territories
and get special visual treatment in the Genre Planet (glow between territories).

Usage:
    python3 cross_genre_bridges.py
    python3 cross_genre_bridges.py --min-genres 3 --top 200

Input:  discoworld_cf.db (public_collections) + discoworld.db (releases + genres)
Output: data/cross_genre_bridges.json
"""

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CF_DB_PATH = DATA_DIR / "discoworld_cf.db"
MAIN_DB_PATH = DATA_DIR / "discoworld.db"
OUTPUT_PATH = DATA_DIR / "cross_genre_bridges.json"


# ---------------------------------------------------------------------------
# Genre clustering from styles
# ---------------------------------------------------------------------------

# Map Discogs styles to broad genre clusters for bridge detection.
# This is intentionally coarse — we want releases that truly bridge
# different musical worlds, not just adjacent subgenres.
STYLE_TO_CLUSTER = {
    # Techno world
    "Techno": "Techno", "Minimal": "Techno", "Industrial": "Techno",
    "Acid": "Techno", "Hard Techno": "Techno", "Dub Techno": "Techno",
    # House world
    "House": "House", "Deep House": "House", "Acid House": "House",
    "Tech House": "House", "Disco": "House", "Nu-Disco": "House",
    "Garage House": "House", "Progressive House": "House",
    # Ambient / Experimental
    "Ambient": "Ambient", "Drone": "Ambient", "Dark Ambient": "Ambient",
    "Experimental": "Ambient", "Noise": "Ambient", "Musique Concrète": "Ambient",
    "Field Recording": "Ambient", "New Age": "Ambient",
    # Electro / Breaks
    "Electro": "Electro", "Breakbeat": "Electro", "Breaks": "Electro",
    "Big Beat": "Electro", "Miami Bass": "Electro",
    # Drum and Bass / Jungle
    "Drum n Bass": "DnB", "Jungle": "DnB", "Liquid Funk": "DnB",
    "Darkstep": "DnB", "Neurofunk": "DnB",
    # Trance
    "Trance": "Trance", "Goa Trance": "Trance", "Psy-Trance": "Trance",
    "Progressive Trance": "Trance", "Euro Trance": "Trance",
    # Downtempo / Trip Hop
    "Downtempo": "Downtempo", "Trip Hop": "Downtempo", "Chillout": "Downtempo",
    "Lounge": "Downtempo", "Leftfield": "Downtempo",
    # Dub / Reggae
    "Dub": "Dub", "Reggae": "Dub", "Dancehall": "Dub",
    "Dubstep": "Dub", "Future Garage": "Dub",
    # IDM / Glitch
    "IDM": "IDM", "Glitch": "IDM", "Clicks & Cuts": "IDM",
    "Abstract": "IDM", "Microsound": "IDM",
    # EBM / Synth
    "EBM": "EBM", "Synth-pop": "EBM", "Coldwave": "EBM",
    "Darkwave": "EBM", "Synthwave": "EBM", "Italo-Disco": "EBM",
    # Hip Hop
    "Hip Hop": "Hip Hop", "Instrumental": "Hip Hop", "Boom Bap": "Hip Hop",
    "Abstract Hip Hop": "Hip Hop",
}


def get_release_clusters(styles_json: str) -> set[str]:
    """Parse styles JSON and return the set of genre clusters."""
    try:
        styles = json.loads(styles_json) if styles_json else []
    except (json.JSONDecodeError, TypeError):
        styles = [s.strip() for s in str(styles_json).split(",") if s.strip()]

    clusters = set()
    for style in styles:
        cluster = STYLE_TO_CLUSTER.get(style)
        if cluster:
            clusters.add(cluster)
    return clusters


# ---------------------------------------------------------------------------
# Bridge detection
# ---------------------------------------------------------------------------


def find_bridge_releases(
    min_genres: int = 2,
    min_users: int = 3,
    top_n: int = 500,
) -> list[dict]:
    """Find releases that bridge multiple genre clusters.

    Algorithm:
    1. For each user in public_collections, determine their genre profile
       (which clusters their releases belong to)
    2. For each release, count how many different genre clusters its owners
       collectively span
    3. A "bridge" release is one owned by users whose OTHER releases
       come from different genre clusters

    Returns sorted list of bridge releases with their connecting genres.
    """
    if not CF_DB_PATH.exists():
        print(f"ERROR: CF database not found at {CF_DB_PATH}")
        print("Run collection_crawler.py first.")
        sys.exit(1)

    if not MAIN_DB_PATH.exists():
        print(f"ERROR: Main database not found at {MAIN_DB_PATH}")
        print("Run build_db.py first.")
        sys.exit(1)

    cf_conn = sqlite3.connect(CF_DB_PATH)
    main_conn = sqlite3.connect(MAIN_DB_PATH)

    # Step 1: Build release -> genre clusters mapping from main DB
    print("Loading release genre clusters...")
    release_clusters: dict[int, set[str]] = {}
    cursor = main_conn.execute("SELECT discogs_id, styles FROM releases WHERE styles IS NOT NULL")
    for row in cursor:
        clusters = get_release_clusters(row[1])
        if clusters:
            release_clusters[row[0]] = clusters

    print(f"  {len(release_clusters):,} releases with genre clusters")

    # Step 2: Build user genre profiles
    print("Building user genre profiles...")
    user_genres: dict[str, set[str]] = defaultdict(set)
    user_releases: dict[str, set[int]] = defaultdict(set)

    cursor = cf_conn.execute("SELECT user_hash, release_id FROM public_collections")
    batch_size = 100_000
    total = 0

    while True:
        batch = cursor.fetchmany(batch_size)
        if not batch:
            break
        for user_hash, release_id in batch:
            user_releases[user_hash].add(release_id)
            clusters = release_clusters.get(release_id, set())
            user_genres[user_hash].update(clusters)
            total += 1

    print(f"  {len(user_genres):,} users with genre profiles")

    # Step 3: For each release, check if its owners span multiple genres
    print("Finding bridge releases...")

    # release_id -> {cluster -> count of users from that cluster who own it}
    bridge_scores: dict[int, Counter] = defaultdict(Counter)
    release_owner_count: Counter = Counter()

    for user_hash, genres in user_genres.items():
        if len(genres) < min_genres:
            continue  # User doesn't span enough genres — not interesting

        for release_id in user_releases[user_hash]:
            # For this release, record which genres this multi-genre user represents
            release_clusters_for_user = release_clusters.get(release_id, set())
            # The "other genres" this user brings (genres from their OTHER releases)
            other_genres = genres - release_clusters_for_user
            for genre in other_genres:
                bridge_scores[release_id][genre] += 1
            release_owner_count[release_id] += 1

    # Step 4: Score and rank
    print("Scoring bridge releases...")
    bridges = []

    for release_id, genre_counts in bridge_scores.items():
        # Must have owners from at least min_genres different clusters
        active_genres = {g for g, c in genre_counts.items() if c >= 1}
        own_genres = release_clusters.get(release_id, set())
        all_connected = active_genres | own_genres

        if len(all_connected) < min_genres:
            continue

        owner_count = release_owner_count[release_id]
        if owner_count < min_users:
            continue

        # Bridge score: number of connected genres * log(owner count)
        import math
        score = len(all_connected) * math.log1p(owner_count)

        bridges.append({
            "release_id": release_id,
            "own_genres": sorted(own_genres),
            "connecting_genres": sorted(all_connected - own_genres),
            "all_genres": sorted(all_connected),
            "genre_count": len(all_connected),
            "owner_count": owner_count,
            "bridge_score": round(score, 3),
        })

    # Sort by bridge score
    bridges.sort(key=lambda x: x["bridge_score"], reverse=True)
    bridges = bridges[:top_n]

    # Enrich with release metadata
    print("Enriching with metadata...")
    if bridges:
        release_ids = [b["release_id"] for b in bridges]
        placeholders = ",".join("?" * len(release_ids))
        meta_rows = main_conn.execute(
            f"""SELECT discogs_id, title, artist, label, year, country
                FROM releases WHERE discogs_id IN ({placeholders})""",
            release_ids,
        ).fetchall()
        meta_map = {r[0]: {
            "title": r[1], "artist": r[2], "label": r[3],
            "year": r[4], "country": r[5],
        } for r in meta_rows}

        for bridge in bridges:
            meta = meta_map.get(bridge["release_id"], {})
            bridge.update(meta)

    cf_conn.close()
    main_conn.close()

    return bridges


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Find cross-genre bridge releases (gateway records)"
    )
    parser.add_argument(
        "--min-genres", type=int, default=2,
        help="Minimum genre clusters a bridge must connect (default: 2)"
    )
    parser.add_argument(
        "--min-users", type=int, default=3,
        help="Minimum multi-genre users owning the release (default: 3)"
    )
    parser.add_argument(
        "--top", type=int, default=500,
        help="Number of top bridge releases to output (default: 500)"
    )
    parser.add_argument(
        "--output", type=str,
        help="Output JSON path (default: data/cross_genre_bridges.json)"
    )
    args = parser.parse_args()

    bridges = find_bridge_releases(
        min_genres=args.min_genres,
        min_users=args.min_users,
        top_n=args.top,
    )

    output_path = Path(args.output) if args.output else OUTPUT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump({
            "meta": {
                "min_genres": args.min_genres,
                "min_users": args.min_users,
                "total_bridges": len(bridges),
            },
            "bridges": bridges,
        }, f, indent=2)

    print(f"\n--- Cross-Genre Bridges ---")
    print(f"Total bridge releases: {len(bridges)}")
    if bridges:
        avg_genres = sum(b["genre_count"] for b in bridges) / len(bridges)
        print(f"Average genres connected: {avg_genres:.1f}")
        print(f"\nTop 10 gateway records:")
        for b in bridges[:10]:
            title = b.get("title", "Unknown")
            artist = b.get("artist", "Unknown")
            genres = " <-> ".join(b["all_genres"])
            print(f"  {artist} - {title} [{genres}] (score: {b['bridge_score']})")

    print(f"\nOutput: {output_path}")


if __name__ == "__main__":
    main()
