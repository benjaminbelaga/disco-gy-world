"""SQLite connection helper for DiscoWorld API.

Two sources, one interface. Callers always get a `sqlite3.Connection` with
`row_factory = sqlite3.Row`, so every route's SQL stays byte-identical whichever
source is live.

1. `data/discoworld.db` — the full corpus, built offline by
   `packages/pipeline/build_db.py` from a Discogs monthly dump. Used when present.

2. An in-memory database hydrated from the JSON the frontend already downloads.
   Used when the corpus file is absent — which is the case in production and has
   been since launch: `discoworld.db` is gitignored, so no deploy has ever
   carried it. Every route gated on `db_available()` returned
   `503 Database not available` — artists, labels, releases, search,
   recommendations, personal_reco, crate_neighbors.

The fallback serves the 5,000-release preview rather than the full corpus. That
is a real reduction in coverage and it is deliberate: a thin, honest answer beats
a 503, and it costs nothing to carry — the file is already deployed and already
fetched by the browser on every visit.

Corpus note (2026-08-11) — correcting the note this docstring carried before.

The 2026-08-06 note said the `mcp-discogs` corpus "does not exist". That was
wrong, and it was wrong twice over: a second session reached the same conclusion
from a different direction five days later. Both were measurement errors worth
naming, because they share a shape.

  - The first queried the Docker container `yoyaku-mcp-postgres` — database
    `yoyaku_knowledge`, 7.8 MB, tables autonomous_actions / incident_history /
    learned_patterns. That is MCP operations telemetry. The container name is a
    near-perfect decoy for the thing it is not.
  - The second read an empty `docker compose ps` in /opt/mcp-discogs as "the
    database is down", and 404s on `/health` and `/search` as "the routes are
    dead". The service does not run in Docker (that compose file is vestigial),
    and the routes are `/healthz` and `/mcp/*`.

Measured 2026-08-11: a native PostgreSQL 18 on localhost:5432, database `mcp`,
73 GB, 15,080,106 rows in `releases`. The corpus is real.

It is also not the corpus this application needs. `releases` is an identity
table — `year` is NULL on every row sampled and `data` is `{}` — built so
`/mcp/resolve/catno` can turn a catalogue number into a release id. A timeline
cannot be drawn from it. `masters` can: 1,012,900 rows, 94% with a year, 98%
with YouTube videos. That is the source `build_db.py --source postgres` reads,
and `data/discoworld.db` now carries 954,703 releases built from it.

The in-memory preview below remains as the fallback, unchanged. It is not a
stopgap: it is what serves the site if the corpus file is ever absent again.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent

DB_PATHS = [
    _ROOT / "data" / "discoworld.db",
]

# The JSON lives at <root>/data/ in production and at packages/web/public/data/
# in a dev checkout. Both are checked; first hit wins.
_JSON_DIRS = [
    _ROOT / "data",
    _ROOT / "packages" / "web" / "public" / "data",
]

_SCHEMA_PATH = _ROOT / "packages" / "pipeline" / "db_schema.sql"

# Schema is inlined because packages/pipeline is not deployed — the server has
# only packages/api and packages/web. db_schema.sql is read in preference when a
# checkout has it; keep the two in sync.
#
# It was also, until 2026-08-06, untracked: a `**/*.sql` rule in the user's
# global gitignore had kept it out of every commit since the repo was created.
# So a fresh clone could not run build_db.py, which is the structural reason no
# deploy ever carried a corpus and every DB route 503'd. It is force-added now.
_SCHEMA_FALLBACK = """
CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    scene TEXT, biome TEXT, year INTEGER, description TEXT
);
CREATE TABLE IF NOT EXISTS genre_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES genres(id),
    target_id INTEGER NOT NULL REFERENCES genres(id),
    link_type TEXT NOT NULL DEFAULT 'influence',
    UNIQUE(source_id, target_id)
);
CREATE TABLE IF NOT EXISTS taxonomy_bridge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discogs_style TEXT NOT NULL,
    genre_id INTEGER NOT NULL REFERENCES genres(id),
    confidence REAL NOT NULL DEFAULT 1.0,
    UNIQUE(discogs_style, genre_id)
);
CREATE TABLE IF NOT EXISTS style_cooccurrence (
    style_a TEXT NOT NULL, style_b TEXT NOT NULL, count INTEGER NOT NULL,
    PRIMARY KEY (style_a, style_b)
);
CREATE TABLE IF NOT EXISTS releases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discogs_id INTEGER UNIQUE,
    title TEXT NOT NULL,
    artist TEXT, label TEXT, catno TEXT, country TEXT,
    year INTEGER, format TEXT, styles TEXT, youtube_url TEXT
);
-- `score` is a similarity (sorted DESC), not a distance — see db_schema.sql.
CREATE TABLE IF NOT EXISTS release_neighbors (
    release_id INTEGER NOT NULL, neighbor_id INTEGER NOT NULL, score REAL NOT NULL,
    PRIMARY KEY (release_id, neighbor_id)
);
CREATE INDEX IF NOT EXISTS idx_genres_slug ON genres(slug);
CREATE INDEX IF NOT EXISTS idx_releases_year ON releases(year);
CREATE INDEX IF NOT EXISTS idx_releases_artist ON releases(artist);
CREATE INDEX IF NOT EXISTS idx_releases_label ON releases(label);
CREATE INDEX IF NOT EXISTS idx_taxonomy_style ON taxonomy_bridge(discogs_style);
"""

# Built once per process, then shared. `check_same_thread=False` because uvicorn
# serves requests from a threadpool and this connection is read-only after
# hydration — no writer, so no cross-thread write hazard.
_memory_conn: sqlite3.Connection | None = None
_memory_failed = False


def get_db_path() -> Path | None:
    """Return the first usable corpus database path, or None.

    A file with zero releases does not count. `build_db.py` creates the schema
    and populates genres before it ingests releases, so an interrupted or
    genres-only build leaves a valid-looking 124 KB database with an empty
    `releases` table — which would shadow the fallback and make local
    development strictly worse than production. Presence is not readiness.

    The probe asks "is there a row", not "how many" — `SELECT 1 ... LIMIT 1`
    rather than `COUNT(*)`. Both answer the readiness question; only one is
    O(1). SQLite has no stored row count, so the count scans the whole table:
    29 ms on the 954,703-row corpus, paid twice per request (`db_available()`
    then `get_db()`), and growing with every rebuild. It was free on the
    5,000-row preview, which is why it survived.
    """
    for path in DB_PATHS:
        if not path.exists():
            continue
        try:
            probe = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            try:
                has_rows = probe.execute("SELECT 1 FROM releases LIMIT 1").fetchone()
            finally:
                probe.close()
        except sqlite3.Error:
            continue
        if has_rows:
            return path
    return None


def _find_json(name: str) -> Path | None:
    for directory in _JSON_DIRS:
        candidate = directory / name
        if candidate.exists():
            return candidate
    return None


def _load_json(name: str):
    path = _find_json(name)
    if path is None:
        return None
    with open(path) as fh:
        return json.load(fh)


def _normalize(name: str) -> str:
    """Lowercase, strip non-alphanumerics. Used only for exact-key matching."""
    return "".join(ch for ch in name.lower() if ch.isalnum())


def _hydrate_genres(conn: sqlite3.Connection, world: dict) -> None:
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
                (genre.get("description") or "")[:500],
            ),
        )
    for link in world.get("links", []):
        conn.execute(
            "INSERT OR IGNORE INTO genre_links (source_id, target_id, link_type) "
            "SELECT g1.id, g2.id, 'influence' FROM genres g1, genres g2 "
            "WHERE g1.slug = ? AND g2.slug = ?",
            (link.get("source"), link.get("target")),
        )


def _hydrate_releases(conn: sqlite3.Connection, preview) -> list[str]:
    """Insert preview releases; return the distinct styles seen.

    Field names differ from the corpus schema because the preview is generated
    for the browser: `id` is the Discogs release id, `youtube` is a full watch
    URL, `vinyl` is a boolean rather than a format string.
    """
    rows = preview.get("releases") if isinstance(preview, dict) else preview
    styles_seen: set[str] = set()
    for r in rows or []:
        styles = r.get("styles") or []
        styles_seen.update(s for s in styles if s)
        catno = r.get("catno")
        # The generator writes the literal string "none" for a missing catno.
        if catno == "none":
            catno = None
        conn.execute(
            "INSERT OR IGNORE INTO releases "
            "(discogs_id, title, artist, label, catno, country, year, format, styles, youtube_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                int(r["id"]) if str(r.get("id", "")).isdigit() else None,
                r.get("title") or "",
                r.get("artist"),
                r.get("label"),
                catno,
                r.get("country"),
                int(r["year"]) if str(r.get("year", "")).isdigit() else 0,
                "Vinyl" if r.get("vinyl") else None,
                json.dumps(styles),
                r.get("youtube"),
            ),
        )
    return sorted(styles_seen)


def _hydrate_taxonomy(conn: sqlite3.Connection, styles: list[str]) -> None:
    """Map Discogs styles to world genres by exact normalized name or `aka`.

    Deliberately exact, not fuzzy. `packages/pipeline/taxonomy_bridge.py` does
    the real fuzzy mapping, but it is not deployed and it needs a
    `data/processed/stats.json` that does not exist here. A conservative subset
    of high-confidence mappings is the right thing for a fallback: it makes the
    timeline's genre chips correct where they appear rather than plausible
    everywhere. The full bridge — including the join to YOYAKU's canonical
    musicstyle vocabulary — is tracked separately as the taxonomy contract.
    """
    index: dict[str, int] = {}
    for row in conn.execute("SELECT id, name FROM genres"):
        index.setdefault(_normalize(row[1]), row[0])
    for row in conn.execute("SELECT id, slug FROM genres"):
        index.setdefault(_normalize(row[1]), row[0])

    for style in styles:
        genre_id = index.get(_normalize(style))
        if genre_id is None:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO taxonomy_bridge (discogs_style, genre_id, confidence) "
            "VALUES (?, ?, ?)",
            (style, genre_id, 1.0),
        )


def _build_memory_db() -> sqlite3.Connection | None:
    world = _load_json("world.json")
    preview = _load_json("releases_preview.json")
    if world is None and preview is None:
        return None

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    schema = _SCHEMA_PATH.read_text() if _SCHEMA_PATH.exists() else _SCHEMA_FALLBACK
    conn.executescript(schema)

    if world:
        _hydrate_genres(conn, world)
    styles = _hydrate_releases(conn, preview) if preview else []
    if world and styles:
        _hydrate_taxonomy(conn, styles)
    conn.commit()
    return conn


def _memory_db() -> sqlite3.Connection | None:
    """Build the in-memory fallback once; None if its inputs are missing too."""
    global _memory_conn, _memory_failed
    if _memory_conn is not None:
        return _memory_conn
    if _memory_failed:
        return None
    try:
        _memory_conn = _build_memory_db()
    except Exception:
        _memory_conn = None
    if _memory_conn is None:
        _memory_failed = True
    return _memory_conn


@contextmanager
def get_db():
    """Yield a read connection. Raises FileNotFoundError if no source at all."""
    db_path = get_db_path()
    if db_path is not None:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
        return

    conn = _memory_db()
    if conn is None:
        raise FileNotFoundError(
            "No DiscoWorld corpus and no preview JSON to fall back to. "
            "Run packages/pipeline/build_db.py, or deploy data/world.json and "
            "data/releases_preview.json."
        )
    # Process-lifetime connection — do not close it on the way out.
    yield conn


def db_available() -> bool:
    """True when a route can query something, corpus or fallback."""
    return get_db_path() is not None or _memory_db() is not None


def db_source() -> str:
    """Which source is live: 'corpus', 'preview', or 'none'. For /api/health."""
    if get_db_path() is not None:
        return "corpus"
    return "preview" if _memory_db() is not None else "none"
