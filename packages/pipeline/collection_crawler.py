"""
Crawl public Discogs collections of electronic vinyl collectors.

Strategy: start from known releases in the DB -> find users who own them
-> fetch their full collections -> store (user_hash, release_id) pairs.

Usage:
    python3 collection_crawler.py --target 1000 --start-release 12345
    python3 collection_crawler.py --target 1000 --resume

Estimated time for 1000 users at 60 req/min: ~8 hours (depends on collection sizes).
"""

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from discogs_client import api_get, DISCOGS_TOKEN, RateLimiter

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CF_DB_PATH = DATA_DIR / "discoworld_cf.db"
MAIN_DB_PATH = DATA_DIR / "discoworld.db"

# Rate limiter shared with discogs_client (but we create our own for isolation)
_limiter = RateLimiter(max_requests=55, window_seconds=60.0)

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

CF_SCHEMA = """
CREATE TABLE IF NOT EXISTS public_collections (
    user_hash TEXT NOT NULL,
    release_id INTEGER NOT NULL,
    PRIMARY KEY (user_hash, release_id)
);

CREATE TABLE IF NOT EXISTS crawl_progress (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS crawled_users (
    user_hash TEXT PRIMARY KEY,
    collection_size INTEGER,
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS seed_releases (
    release_id INTEGER PRIMARY KEY,
    processed INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pc_release ON public_collections(release_id);
CREATE INDEX IF NOT EXISTS idx_pc_user ON public_collections(user_hash);
"""


def init_cf_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Create or open the collaborative filtering database."""
    path = db_path or CF_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(CF_SCHEMA)
    return conn


def hash_username(username: str) -> str:
    """Hash a Discogs username for privacy."""
    return hashlib.sha256(username.lower().encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Seed releases
# ---------------------------------------------------------------------------


def load_seed_releases(conn: sqlite3.Connection, start_release: int | None = None) -> list[int]:
    """Load seed release IDs from the main DiscoWorld DB.

    If start_release is given, use it as the single seed.
    Otherwise, pick popular vinyl releases from the main DB.
    """
    existing = conn.execute("SELECT COUNT(*) FROM seed_releases").fetchone()[0]
    if existing > 0:
        # Already have seeds, return unprocessed ones
        rows = conn.execute(
            "SELECT release_id FROM seed_releases WHERE processed = 0 LIMIT 100"
        ).fetchall()
        return [r[0] for r in rows]

    if start_release:
        conn.execute(
            "INSERT OR IGNORE INTO seed_releases (release_id) VALUES (?)",
            (start_release,),
        )
        conn.commit()
        return [start_release]

    # Pull popular releases from main DB (ones likely to have many collectors)
    if not MAIN_DB_PATH.exists():
        print("ERROR: Main database not found at", MAIN_DB_PATH)
        print("Provide --start-release or run build_db.py first.")
        sys.exit(1)

    main_conn = sqlite3.connect(MAIN_DB_PATH)
    # Get well-known electronic vinyl releases (high chance of public collectors)
    rows = main_conn.execute(
        """SELECT discogs_id FROM releases
           WHERE format = 'Vinyl' AND year > 1990 AND year < 2025
           ORDER BY RANDOM() LIMIT 200"""
    ).fetchall()
    main_conn.close()

    seeds = [r[0] for r in rows if r[0]]
    for seed in seeds:
        conn.execute(
            "INSERT OR IGNORE INTO seed_releases (release_id) VALUES (?)", (seed,)
        )
    conn.commit()
    print(f"Loaded {len(seeds)} seed releases from main DB")
    return seeds


# ---------------------------------------------------------------------------
# Discogs API helpers
# ---------------------------------------------------------------------------


def fetch_release_collectors(release_id: int, page: int = 1) -> dict:
    """Fetch users who have a release in their collection (community/contributors).

    Uses the release stats endpoint which shows collectors.
    """
    _limiter.wait()
    return api_get(
        f"/releases/{release_id}/stats",
    )


def fetch_community_contributors(release_id: int, page: int = 1) -> list[str]:
    """Get usernames of users who have this release via the community rating endpoint.

    Discogs doesn't have a direct "who owns this" API, so we use
    the release page community contributors (users who submitted data).
    Alternative: we check marketplace listings to find sellers (= likely owners).
    """
    # The most reliable way: fetch users from the release's community
    # /releases/{id} includes community.contributors
    _limiter.wait()
    try:
        data = api_get(f"/releases/{release_id}")
        # contributors is a list of {username, resource_url}
        contributors = data.get("contributors", [])
        return [c.get("username", "") for c in contributors if c.get("username")]
    except Exception:
        return []


def fetch_marketplace_sellers(release_id: int) -> list[str]:
    """Get seller usernames from marketplace listings for a release."""
    _limiter.wait()
    try:
        data = api_get(
            f"/marketplace/listings",
            params={"release_id": release_id, "per_page": 50},
        )
        listings = data.get("listings", [])
        sellers = set()
        for listing in listings:
            seller = listing.get("seller", {}).get("username", "")
            if seller:
                sellers.add(seller)
        return list(sellers)
    except Exception:
        return []


def discover_users_from_release(release_id: int) -> list[str]:
    """Find Discogs users associated with a release (contributors + sellers)."""
    users = set()

    # Method 1: contributors (people who edited the release page)
    contributors = fetch_community_contributors(release_id)
    users.update(contributors)

    # Method 2: marketplace sellers (likely own the release)
    if len(users) < 5:
        sellers = fetch_marketplace_sellers(release_id)
        users.update(sellers)

    return list(users)


def fetch_user_collection_page(
    username: str, page: int = 1, per_page: int = 100
) -> dict | None:
    """Fetch a page of a user's public collection."""
    _limiter.wait()
    try:
        data = api_get(
            f"/users/{username}/collection/folders/0/releases",
            params={"page": page, "per_page": per_page, "sort": "added", "sort_order": "desc"},
        )
        return data
    except Exception as e:
        if "403" in str(e) or "404" in str(e):
            return None  # Private or nonexistent
        raise


# ---------------------------------------------------------------------------
# Crawler
# ---------------------------------------------------------------------------


def crawl_user(conn: sqlite3.Connection, username: str) -> int:
    """Crawl a single user's public collection. Returns number of releases stored."""
    user_hash = hash_username(username)

    # Skip if already crawled
    existing = conn.execute(
        "SELECT 1 FROM crawled_users WHERE user_hash = ?", (user_hash,)
    ).fetchone()
    if existing:
        return 0

    page = 1
    total_stored = 0

    while True:
        data = fetch_user_collection_page(username, page=page)
        if data is None:
            # Private or not found — mark as crawled with 0 items
            conn.execute(
                "INSERT OR REPLACE INTO crawled_users (user_hash, collection_size) VALUES (?, 0)",
                (user_hash,),
            )
            conn.commit()
            return 0

        releases = data.get("releases", [])
        if not releases:
            break

        batch = []
        for rel in releases:
            basic = rel.get("basic_information", {})
            rid = basic.get("id") or rel.get("id")
            if rid:
                batch.append((user_hash, rid))

        if batch:
            conn.executemany(
                "INSERT OR IGNORE INTO public_collections (user_hash, release_id) VALUES (?, ?)",
                batch,
            )
            total_stored += len(batch)

        pagination = data.get("pagination", {})
        total_pages = pagination.get("pages", 1)

        # Limit: don't crawl collections > 5000 items (likely dealers, not collectors)
        total_items = pagination.get("items", 0)
        if total_items > 5000:
            print(f"    Skipping {username}: collection too large ({total_items} items)")
            break

        if page >= total_pages:
            break
        page += 1

    # Mark user as crawled
    conn.execute(
        "INSERT OR REPLACE INTO crawled_users (user_hash, collection_size) VALUES (?, ?)",
        (user_hash, total_stored),
    )
    conn.commit()

    return total_stored


def run_crawler(
    target_users: int = 1000,
    start_release: int | None = None,
    db_path: Path | None = None,
):
    """Main crawler loop.

    1. Load seed releases
    2. For each seed, discover users
    3. Crawl each user's collection
    4. Use discovered releases as new seeds (snowball)
    5. Stop when target_users reached
    """
    conn = init_cf_db(db_path)

    # Check progress
    crawled_count = conn.execute("SELECT COUNT(*) FROM crawled_users WHERE collection_size > 0").fetchone()[0]
    print(f"Resuming: {crawled_count} users already crawled")

    if crawled_count >= target_users:
        print(f"Target of {target_users} users already reached!")
        _print_stats(conn)
        conn.close()
        return

    seeds = load_seed_releases(conn, start_release)
    if not seeds:
        print("No seed releases available. Provide --start-release.")
        conn.close()
        return

    print(f"Starting crawler with {len(seeds)} seed releases, target: {target_users} users")
    users_discovered: set[str] = set()
    seed_idx = 0

    while crawled_count < target_users and seed_idx < len(seeds):
        seed_id = seeds[seed_idx]
        seed_idx += 1

        print(f"\n[Seed {seed_idx}/{len(seeds)}] Release {seed_id}")

        # Discover users from this seed release
        new_users = discover_users_from_release(seed_id)
        print(f"  Found {len(new_users)} users")

        # Mark seed as processed
        conn.execute(
            "UPDATE seed_releases SET processed = 1 WHERE release_id = ?",
            (seed_id,),
        )
        conn.commit()

        for username in new_users:
            if crawled_count >= target_users:
                break

            if username in users_discovered:
                continue
            users_discovered.add(username)

            print(f"  Crawling {username}... ", end="", flush=True)
            try:
                count = crawl_user(conn, username)
                if count > 0:
                    crawled_count += 1
                    print(f"{count} releases [{crawled_count}/{target_users}]")

                    # Snowball: add some of this user's releases as new seeds
                    if crawled_count < target_users and len(seeds) < 500:
                        user_hash = hash_username(username)
                        new_seeds = conn.execute(
                            """SELECT release_id FROM public_collections
                               WHERE user_hash = ?
                               ORDER BY RANDOM() LIMIT 3""",
                            (user_hash,),
                        ).fetchall()
                        for ns in new_seeds:
                            if ns[0] not in seeds:
                                seeds.append(ns[0])
                                conn.execute(
                                    "INSERT OR IGNORE INTO seed_releases (release_id) VALUES (?)",
                                    (ns[0],),
                                )
                        conn.commit()
                else:
                    print("skipped (private/empty)")
            except Exception as e:
                print(f"error: {e}")
                continue

        # Reload seeds if running low
        if seed_idx >= len(seeds) - 1:
            more_seeds = conn.execute(
                "SELECT release_id FROM seed_releases WHERE processed = 0 LIMIT 50"
            ).fetchall()
            for s in more_seeds:
                if s[0] not in seeds:
                    seeds.append(s[0])

    print(f"\nCrawling complete!")
    _print_stats(conn)
    conn.close()


def _print_stats(conn: sqlite3.Connection):
    """Print crawler statistics."""
    users = conn.execute("SELECT COUNT(*) FROM crawled_users WHERE collection_size > 0").fetchone()[0]
    pairs = conn.execute("SELECT COUNT(*) FROM public_collections").fetchone()[0]
    unique_releases = conn.execute("SELECT COUNT(DISTINCT release_id) FROM public_collections").fetchone()[0]
    avg_size = conn.execute("SELECT AVG(collection_size) FROM crawled_users WHERE collection_size > 0").fetchone()[0]

    print(f"\n--- Crawler Stats ---")
    print(f"Users crawled:    {users:,}")
    print(f"Total pairs:      {pairs:,}")
    print(f"Unique releases:  {unique_releases:,}")
    print(f"Avg collection:   {avg_size:.0f} releases" if avg_size else "Avg collection:   N/A")
    print(f"DB size:          {CF_DB_PATH.stat().st_size / 1024 / 1024:.1f} MB" if CF_DB_PATH.exists() else "")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Crawl public Discogs collections for collaborative filtering"
    )
    parser.add_argument(
        "--target", type=int, default=1000,
        help="Target number of users to crawl (default: 1000)"
    )
    parser.add_argument(
        "--start-release", type=int,
        help="Discogs release ID to start discovery from"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from last crawl progress"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Print stats and exit"
    )
    parser.add_argument(
        "--db-path", type=str,
        help="Custom database path"
    )
    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else None

    if args.stats:
        conn = init_cf_db(db_path)
        _print_stats(conn)
        conn.close()
        return

    run_crawler(
        target_users=args.target,
        start_release=args.start_release,
        db_path=db_path,
    )


if __name__ == "__main__":
    main()
