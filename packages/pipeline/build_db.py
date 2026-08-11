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


def stamp_carried_by_catno(conn: sqlite3.Connection) -> int:
    """Mark corpus releases we carry, matching on catalogue number.

    The Discogs release id is a *pressing* id. The same record exists under many
    of them, so a shop product and a corpus entry for the same music almost
    never share one unless they were sourced identically. Measured 2026-08-11:
    joining the shop's 10,178 catalogue numbers to the corpus by release id
    matched **618**; joining by normalized catalogue number matched **7,545**.
    Twelve times the coverage, for the same question — "do we have this record".

    That is the whole reason the YOYAKU bridge felt empty. It was not missing
    code; it was joined on the wrong key.

    Guards against a wrong stamp:
      - normalized catalogue numbers shorter than 4 characters are skipped.
        "001" or "EP2" collide across unrelated labels; a real catalogue number
        carries a label prefix.
      - rows already stamped by release id are left alone — that match is exact
        and strictly stronger than this one.
    """

    def normalize(catno: str) -> str:
        return "".join(ch for ch in catno.upper() if ch.isalnum())

    shop_by_catno: dict[str, tuple] = {}
    try:
        for r in stream_releases_from_shop():
            sku = r.get("sku")
            if not sku:
                continue
            key = normalize(sku)
            if len(key) >= 4:
                shop_by_catno.setdefault(key, (sku, r.get("shop_url")))
    except (ImportError, FileNotFoundError):
        return 0

    if not shop_by_catno:
        return 0

    updates = []
    for rid, catno in conn.execute(
        "SELECT id, catno FROM releases "
        "WHERE shop_url IS NULL AND catno IS NOT NULL AND catno != ''"
    ):
        hit = shop_by_catno.get(normalize(catno))
        if hit:
            updates.append((hit[0], hit[1], rid))

    conn.executemany("UPDATE releases SET sku = ?, shop_url = ? WHERE id = ?", updates)
    conn.commit()
    return len(updates)


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


def stream_releases_from_shop() -> "list[dict]":
    """Yield the YOYAKU catalogue, in the JSONL dump's shape, carrying sku + shop_url.

    Produced by `export_shop_catalogue.php` on the shop host; this reads the JSON
    artifact, so the build never depends on reaching a second machine.

    This is what makes "we have this record" a column instead of a per-render
    API call — and, more to the point, what makes it visible at all. Measured
    2026-08-11: of the shop's 10,236 discogs-identified products, only 618 were
    present in the Postgres corpus. Adding the catalogue as a source is the
    difference between a shop that is 6% visible in the world and one that is
    wholly visible.

    Most of these carry no year (the shop does not maintain one), so they will
    not appear on the timeline. They do appear in genre panels, in search, and
    under their label and artist — which is where someone would meet them.
    """
    for directory in (DATA_DIR, Path(__file__).resolve().parent.parent / "web" / "public" / "data"):
        path = directory / "shop_catalogue.json"
        if not path.exists():
            continue
        with open(path) as fh:
            payload = json.load(fh)
        for r in payload.get("releases") or []:
            record = {
                "id": r.get("discogs_id"),
                "title": r.get("title") or "",
                "artists": [{"name": r["artist"]}] if r.get("artist") else [{}],
                "country": r.get("country"),
                "year": r.get("year") or 0,
                "styles": r.get("styles") or [],
                "videos": [],
                "sku": r.get("sku"),
                "shop_url": r.get("shop_url"),
            }
            if r.get("label"):
                record["labels"] = [{"name": r["label"], "catno": r.get("sku") or ""}]
            yield record
        return
    raise FileNotFoundError("shop_catalogue.json not found")


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
    elif source == "shop":
        releases = stream_releases_from_shop()
        if sample_size:
            releases = islice(releases, sample_size)
    else:
        from style_cooccurrence import stream_releases

        releases = stream_releases()
        if sample_size:
            releases = islice(releases, sample_size)

    _COLUMNS = (
        "(discogs_id, title, artist, label, catno, country, year, format, styles, "
        "youtube_url, sku, shop_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    if source == "shop":
        # The shop runs last and must not lose to rows already present: 618 of
        # its records also came from Postgres, richer (year, YouTube). Plain
        # INSERT OR IGNORE would drop the shop row entirely and leave exactly
        # those releases — the ones both in the world and on the shelf —
        # unmarked. So new records insert, and existing ones only get stamped
        # with the two columns the shop owns.
        insert_sql = (
            "INSERT INTO releases " + _COLUMNS +
            " ON CONFLICT(discogs_id) DO UPDATE SET "
            "sku = excluded.sku, shop_url = excluded.shop_url"
        )
    else:
        insert_sql = "INSERT OR IGNORE INTO releases " + _COLUMNS

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
            r.get("sku"),
            r.get("shop_url"),
        ))
        if len(batch) >= 10000:
            conn.executemany(insert_sql, batch)
            conn.commit()
            batch = []
            if (i + 1) % 100000 == 0:
                print(f"  ... {i + 1:,} releases loaded")

    if batch:
        conn.executemany(insert_sql, batch)
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
        choices=["jsonl", "postgres", "preview", "shop"],
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

    # Phase 4c: the YOYAKU catalogue, last so that it stamps sku/shop_url onto
    # rows the richer sources already placed (see the upsert in populate_releases).
    if args.source != "shop":
        try:
            populate_releases(conn, source="shop")
            # Two numbers, because one of them flatters. Every shop row carries a
            # shop_url by construction, so a bare count of them says nothing
            # about the bridge. What matters is how many releases that came from
            # *elsewhere* turned out to be records we sell.
            marked = conn.execute(
                "SELECT COUNT(*) FROM releases WHERE shop_url IS NOT NULL"
            ).fetchone()[0]
            by_catno = stamp_carried_by_catno(conn)
            print(
                f"Carried by YOYAKU: {marked:,} rows carry a shop link "
                f"(mostly the catalogue's own), +{by_catno:,} corpus releases "
                f"matched by catalogue number"
            )
        except (ImportError, FileNotFoundError) as e:
            print(f"Skipping shop merge: {e}")

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
