"""Release artwork resolution, cached.

The Discogs monthly data dumps carry no image URLs — not in `discoworld.db`, not
in `releases_preview.json`, not in any dump-derived corpus. Cover art exists only
behind the live Discogs API, which is capped at 60 requests/minute
(25 unauthenticated). A ten-row genre panel would burn a fifth of that budget per
view, so the cache is not an optimization here: it is what makes the feature
possible at all.

Cache lives in its own SQLite beside the user DB and is created on first use.
Both outcomes are stored: a hit keeps the URLs, a miss is remembered too, so a
release Discogs has no art for is not re-requested on every render. Misses expire
sooner than hits because art gets added to Discogs over time, while an existing
cover URL is effectively permanent.
"""

from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

import httpx

from . import discogs_client

_ROOT = Path(__file__).resolve().parent.parent.parent
_CACHE_PATHS = [_ROOT / "data" / "artwork_cache.db"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS artwork (
    release_id INTEGER PRIMARY KEY,
    thumb TEXT,
    cover TEXT,
    status TEXT NOT NULL,      -- 'ok' | 'missing'
    fetched_at REAL NOT NULL
);
"""

HIT_TTL = 60 * 60 * 24 * 90    # 90d — a cover URL that exists does not change
MISS_TTL = 60 * 60 * 24 * 7    # 7d  — art does get added to Discogs later


def _cache_path() -> Path:
    for path in _CACHE_PATHS:
        if path.parent.exists():
            return path
    _CACHE_PATHS[0].parent.mkdir(parents=True, exist_ok=True)
    return _CACHE_PATHS[0]


@contextmanager
def _cache():
    conn = sqlite3.connect(_cache_path())
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(_SCHEMA)
        yield conn
    finally:
        conn.close()


def _fresh(row: sqlite3.Row, now: float) -> bool:
    ttl = HIT_TTL if row["status"] == "ok" else MISS_TTL
    return (now - row["fetched_at"]) < ttl


def _fetch_one(release_id: int) -> dict:
    """Ask Discogs. Never raises — a failure is a miss, not a 500."""
    try:
        data = discogs_client.api_get(f"/releases/{release_id}")
    except (httpx.HTTPError, ValueError):
        return {"thumb": None, "cover": None, "status": "missing"}

    thumb = data.get("thumb") or None
    images = data.get("images") or []
    cover = None
    if images:
        first = images[0]
        cover = first.get("uri") or first.get("uri150") or None
        thumb = thumb or first.get("uri150")
    return {
        "thumb": thumb,
        "cover": cover,
        "status": "ok" if (thumb or cover) else "missing",
    }


def resolve(release_ids: list[int], allow_fetch: bool = True) -> dict[int, dict]:
    """Return {release_id: {thumb, cover, status, source}} for the ids given.

    `source` is 'cache' or 'discogs', so a caller can see how much of a response
    cost real API budget. With `allow_fetch=False` only cached entries come back —
    useful for a warm-path render that must not block on the network.
    """
    now = time.time()
    out: dict[int, dict] = {}
    missing: list[int] = []

    with _cache() as conn:
        if release_ids:
            marks = ",".join("?" for _ in release_ids)
            rows = conn.execute(
                f"SELECT * FROM artwork WHERE release_id IN ({marks})",
                release_ids,
            ).fetchall()
            cached = {r["release_id"]: r for r in rows}
        else:
            cached = {}

        for rid in release_ids:
            row = cached.get(rid)
            if row is not None and _fresh(row, now):
                out[rid] = {
                    "thumb": row["thumb"],
                    "cover": row["cover"],
                    "status": row["status"],
                    "source": "cache",
                }
            else:
                missing.append(rid)

        if not allow_fetch:
            return out

        for rid in missing:
            result = _fetch_one(rid)
            conn.execute(
                "INSERT OR REPLACE INTO artwork (release_id, thumb, cover, status, fetched_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (rid, result["thumb"], result["cover"], result["status"], now),
            )
            out[rid] = {**result, "source": "discogs"}
        conn.commit()

    return out
