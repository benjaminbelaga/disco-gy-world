"""
Orchestrator: runs all pipeline steps and builds unified SQLite database.

Usage: python3 build_db.py [--sample N] [--skip-similarity]
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

# Ensure sibling modules (taxonomy_bridge, style_cooccurrence, etc.) are importable
sys.path.insert(0, str(Path(__file__).parent))

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DATA_DIR / "discoworld.db"


def create_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Create database and apply schema."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    schema_path = Path(__file__).parent / "db_schema.sql"
    with open(schema_path) as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


def populate_genres(conn: sqlite3.Connection) -> None:
    """Load genres and links from world.json into the database."""
    world_path = Path(__file__).resolve().parent.parent / "web" / "public" / "data" / "world.json"
    with open(world_path) as f:
        world = json.load(f)

    for genre in world.get("genres", []):
        conn.execute(
            "INSERT OR REPLACE INTO genres (name, slug, scene, biome, year, description) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                genre["name"],
                genre["slug"],
                genre.get("scene"),
                genre.get("biome"),
                genre.get("year"),
                genre.get("description", "")[:500],
            ),
        )

    for link in world.get("links", []):
        conn.execute(
            "INSERT OR IGNORE INTO genre_links (source_id, target_id, link_type) "
            "SELECT g1.id, g2.id, 'influence' FROM genres g1, genres g2 "
            "WHERE g1.slug = ? AND g2.slug = ?",
            (link["source"], link["target"]),
        )

    conn.commit()
    genre_count = conn.execute("SELECT COUNT(*) FROM genres").fetchone()[0]
    link_count = conn.execute("SELECT COUNT(*) FROM genre_links").fetchone()[0]
    print(f"Loaded {genre_count} genres, {link_count} links")


def populate_taxonomy(conn: sqlite3.Connection) -> None:
    """Load taxonomy bridge into database. Requires taxonomy_bridge module."""
    from taxonomy_bridge import build_bridge

    bridge = build_bridge()
    for style, genres in bridge["style_to_genres"].items():
        for genre in genres:
            conn.execute(
                "INSERT OR IGNORE INTO taxonomy_bridge (discogs_style, genre_id, confidence) "
                "SELECT ?, id, 1.0 FROM genres WHERE name = ?",
                (style, genre),
            )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM taxonomy_bridge").fetchone()[0]
    print(f"Loaded taxonomy bridge: {count} mappings")


def populate_taxonomy_exact(conn: sqlite3.Connection) -> int:
    """Bridge styles to genres by exact normalized name, from styles actually present.

    The fuzzy bridge (`populate_taxonomy`) needs taxonomy_bridge.py plus a
    `data/processed/stats.json` that only exists where a Discogs dump was
    unpacked — never on the build host. Without a fallback the built corpus
    would ship an empty `taxonomy_bridge`, and the artist timeline would render
    every release with no genre: strictly worse than the 5,000-row preview,
    which does derive a bridge this way.

    Same conservative rule as `packages/api/db.py::_hydrate_taxonomy` — exact
    match on a normalized name or slug, never fuzzy. Correct where it fires
    beats plausible everywhere. The two implementations are deliberate: the API
    package is deployed and the pipeline is not, so they cannot share a module.
    Keep the normalization identical if either changes.
    """

    def normalize(name: str) -> str:
        return "".join(ch for ch in name.lower() if ch.isalnum())

    index: dict[str, int] = {}
    for row in conn.execute("SELECT id, name FROM genres"):
        index.setdefault(normalize(row[1]), row[0])
    for row in conn.execute("SELECT id, slug FROM genres"):
        index.setdefault(normalize(row[1]), row[0])

    styles_seen: set[str] = set()
    for (styles_json,) in conn.execute("SELECT styles FROM releases WHERE styles IS NOT NULL"):
        try:
            styles_seen.update(s for s in json.loads(styles_json) if s)
        except (json.JSONDecodeError, TypeError):
            continue

    added = 0
    for style in sorted(styles_seen):
        genre_id = index.get(normalize(style))
        if genre_id is None:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO taxonomy_bridge (discogs_style, genre_id, confidence) "
            "VALUES (?, ?, ?)",
            (style, genre_id, 1.0),
        )
        added += 1
    conn.commit()
    return added


def populate_cooccurrence(conn: sqlite3.Connection) -> None:
    """Load style co-occurrence matrix. Requires style_cooccurrence module."""
    from style_cooccurrence import build_cooccurrence

    matrix = build_cooccurrence()
    top_pairs = sorted(matrix.items(), key=lambda x: -x[1])[:2000]
    for (a, b), count in top_pairs:
        conn.execute(
            "INSERT OR REPLACE INTO style_cooccurrence VALUES (?, ?, ?)",
            (a, b, count),
        )
    conn.commit()
    print(f"Loaded {len(top_pairs)} style co-occurrence pairs")


def stream_releases_from_preview() -> "list[dict]":
    """Yield the curated preview releases, in the JSONL dump's shape.

    `releases_preview.json` is a hand-picked electronic selection — the records
    DiscoWorld exists to show. The Postgres corpus is broader but not a
    superset: of the preview's 5,000 releases only 218 survive there, because
    `masters` only holds what a YouTube enrichment pass reached. Building from
    Postgres alone would trade 4,782 curated records for a million general ones
    and quietly lose the curation.

    So the corpus is the union. `INSERT OR IGNORE` on discogs_id makes the merge
    idempotent and order-independent.
    """
    for directory in (DATA_DIR, Path(__file__).resolve().parent.parent / "web" / "public" / "data"):
        path = directory / "releases_preview.json"
        if not path.exists():
            continue
        with open(path) as fh:
            payload = json.load(fh)
        rows = payload.get("releases") if isinstance(payload, dict) else payload
        for r in rows or []:
            catno = r.get("catno")
            record = {
                "id": r.get("id"),
                "title": r.get("title") or "",
                "artists": [{"name": r.get("artist")}] if r.get("artist") else [{}],
                "country": r.get("country"),
                "year": r.get("year"),
                "styles": r.get("styles") or [],
                # The preview stores one watch URL; the dump stores a video list.
                "videos": [{"uri": r["youtube"]}] if r.get("youtube") else [],
            }
            if r.get("label"):
                # The generator writes the literal string "none" for a missing catno.
                record["labels"] = [{"name": r["label"], "catno": "" if catno == "none" else (catno or "")}]
            if r.get("vinyl"):
                record["formats"] = [{"name": "Vinyl"}]
            yield record
        return
    raise FileNotFoundError("releases_preview.json not found")


def populate_releases(
    conn: sqlite3.Connection,
    sample_size: int | None = None,
    source: str = "jsonl",
) -> None:
    """Load releases into the database from `source`.

    Three sources, one insert path and one schema:

    - `jsonl`    — the Discogs monthly dump streamed by style_cooccurrence.
                   The original source; absent from every host we deploy to.
    - `postgres` — the `mcp` corpus (masters), see pipeline/postgres_source.py.
    - `preview`  — the curated 5,000 shipped with the frontend.

    Each yields the same dict shape, so nothing below changes.
    """
    from itertools import islice

    if source == "postgres":
        from postgres_source import stream_releases_from_postgres

        releases = stream_releases_from_postgres(limit=sample_size)
    elif source == "preview":
        releases = stream_releases_from_preview()
        if sample_size:
            releases = islice(releases, sample_size)
    else:
        from style_cooccurrence import stream_releases

        releases = stream_releases()
        if sample_size:
            releases = islice(releases, sample_size)

    batch = []
    for i, r in enumerate(releases):
        videos = r.get("videos", [])
        youtube = next(
            (v["uri"] for v in videos if "youtube" in v.get("uri", "")), None
        )
        batch.append((
            r.get("id"),
            r.get("title", ""),
            r.get("artists", [{}])[0].get("name", ""),
            r.get("labels", [{}])[0].get("name", ""),
            r.get("labels", [{}])[0].get("catno", ""),
            r.get("country", ""),
            r.get("year", 0),
            r.get("formats", [{}])[0].get("name", ""),
            json.dumps(r.get("styles", [])),
            youtube,
        ))
        if len(batch) >= 10000:
            conn.executemany(
                "INSERT OR IGNORE INTO releases "
                "(discogs_id, title, artist, label, catno, country, year, format, styles, youtube_url) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                batch,
            )
            conn.commit()
            batch = []
            if (i + 1) % 100000 == 0:
                print(f"  ... {i + 1:,} releases loaded")

    if batch:
        conn.executemany(
            "INSERT OR IGNORE INTO releases "
            "(discogs_id, title, artist, label, catno, country, year, format, styles, youtube_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            batch,
        )
        conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
    print(f"Loaded {total:,} releases")


def main():
    parser = argparse.ArgumentParser(description="Build DiscoWorld unified database")
    parser.add_argument("--sample", type=int, help="Limit releases to N for testing")
    parser.add_argument(
        "--skip-similarity", action="store_true", help="Skip similarity index (slow)"
    )
    parser.add_argument("--db-path", type=str, help="Custom database path")
    parser.add_argument(
        "--source",
        choices=["jsonl", "postgres"],
        default="jsonl",
        help="Where releases come from (default: jsonl, the Discogs dump)",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else DB_PATH
    print(f"Building DiscoWorld database at {db_path}")

    conn = create_db(db_path)

    # Phase 1: genres from world.json (always available)
    populate_genres(conn)

    # Phase 2: taxonomy bridge (requires taxonomy_bridge.py + data)
    try:
        populate_taxonomy(conn)
    except (ImportError, FileNotFoundError) as e:
        print(f"Skipping taxonomy bridge: {e}")

    # Phase 3: co-occurrence (requires style_cooccurrence.py + JSONL data)
    try:
        populate_cooccurrence(conn)
    except (ImportError, FileNotFoundError) as e:
        print(f"Skipping co-occurrence: {e}")

    # Phase 4: releases (JSONL dump, or the mcp Postgres corpus)
    try:
        populate_releases(conn, sample_size=args.sample, source=args.source)
    except (ImportError, FileNotFoundError) as e:
        print(f"Skipping releases: {e}")

    # Phase 4a: merge the curated preview on top. It is not a subset of any
    # other source — see stream_releases_from_preview — and INSERT OR IGNORE
    # means whichever ran first keeps the row.
    if args.source != "preview":
        try:
            populate_releases(conn, source="preview")
        except (ImportError, FileNotFoundError) as e:
            print(f"Skipping preview merge: {e}")

    # Phase 4b: taxonomy fallback. Runs after releases because it derives the
    # bridge from the styles actually loaded — so it cannot run at phase 2.
    bridge_count = conn.execute("SELECT COUNT(*) FROM taxonomy_bridge").fetchone()[0]
    if bridge_count == 0:
        added = populate_taxonomy_exact(conn)
        print(f"Taxonomy bridge (exact-match fallback): {added} mappings")

    # Phase 5: similarity index (requires scikit-learn + releases)
    if not args.skip_similarity:
        try:
            from similarity_index import build_and_store_neighbors

            print("Building similarity index... (this may take a while)")
            build_and_store_neighbors(conn)
        except (ImportError, FileNotFoundError) as e:
            print(f"Skipping similarity index: {e}")

    conn.close()
    if db_path.exists():
        size_mb = db_path.stat().st_size / 1024 / 1024
        print(f"Done! Database: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
