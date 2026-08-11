"""Artist endpoints — releases and timeline for a given artist."""

import json

from fastapi import APIRouter, HTTPException, Query

from ..db import get_db, db_available

router = APIRouter(prefix="/api/artists", tags=["artists"])


@router.get("/{name}/releases")
def artist_releases(
    name: str,
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """All releases from a given artist (case-insensitive substring match)."""
    if not db_available():
        raise HTTPException(503, "Database not available.")

    with get_db() as conn:
        # Same exact-first rule as the timeline (see _artist_rows), decided once
        # so the count and the page cannot disagree about which artists they are
        # describing.
        exact = conn.execute(
            "SELECT 1 FROM releases WHERE artist = ? LIMIT 1", (name,)
        ).fetchone()
        predicate, needle = ("artist = ?", name) if exact else ("artist LIKE ?", f"%{name}%")

        total = conn.execute(
            f"SELECT COUNT(*) FROM releases WHERE {predicate}", (needle,)
        ).fetchone()[0]

        rows = conn.execute(
            f"SELECT * FROM releases WHERE {predicate} ORDER BY year DESC LIMIT ? OFFSET ?",
            (needle, limit, offset),
        ).fetchall()

        return {
            "artist": name,
            "releases": [dict(r) for r in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


# A timeline is a drawing, not an export. Past a few hundred points it stops
# being readable and starts being a payload, so the query is bounded.
#
# The bound is not cosmetic at corpus scale: `artist LIKE '%a%'` matches 648,042
# of the 954,703 rows, and the loop below used to issue one taxonomy query per
# style per row. Unbounded, that single request would have run for minutes and
# returned tens of megabytes. On the 5,000-row preview the same code was
# harmless, which is exactly why it survived to be found here.
TIMELINE_MAX_RELEASES = 500


def _artist_rows(conn, name: str, sql_exact: str, sql_like: str, params_tail: tuple):
    """Fetch an artist's rows, exact name first, substring only if that is empty.

    Both routes here document a substring match, and the frontend has never used
    one: it links out of a release whose artist field it already holds, so the
    parameter is a whole name. That distinction is worth 600×.

    `artist = ?` uses idx_releases_artist and returns in 2ms. `artist LIKE
    '%name%'` cannot use any index and scans all 954,703 rows for 1,247ms — the
    cost of a leading wildcard, and invisible until the corpus stopped being
    5,000 rows. Falling back preserves the substring behaviour for the partial
    queries the routes promise, and nothing calls them that way today.
    """
    rows = conn.execute(sql_exact, (name, *params_tail)).fetchall()
    if rows:
        return rows
    return conn.execute(sql_like, (f"%{name}%", *params_tail)).fetchall()


@router.get("/{name}/timeline")
def artist_timeline(name: str):
    """Releases sorted by year with genre mappings for timeline visualization."""
    if not db_available():
        raise HTTPException(503, "Database not available.")

    with get_db() as conn:
        rows = _artist_rows(
            conn,
            name,
            "SELECT * FROM releases WHERE artist = ? AND year > 0 "
            "ORDER BY year ASC LIMIT ?",
            "SELECT * FROM releases WHERE artist LIKE ? AND year > 0 "
            "ORDER BY year ASC LIMIT ?",
            (TIMELINE_MAX_RELEASES,),
        )

        # One query for the whole bridge instead of one per style per row. The
        # table holds a few dozen mappings; the loop below reads it thousands of
        # times.
        style_genres: dict[str, list[dict]] = {}
        for style, gname, gslug in conn.execute(
            "SELECT tb.discogs_style, g.name, g.slug FROM taxonomy_bridge tb "
            "JOIN genres g ON tb.genre_id = g.id"
        ):
            style_genres.setdefault(style, []).append({"name": gname, "slug": gslug})

        timeline = []
        all_genres = set()

        for row in rows:
            r = dict(row)
            styles = []
            try:
                styles = json.loads(r.get("styles", "[]")) if r.get("styles") else []
            except (json.JSONDecodeError, TypeError):
                pass

            # Map styles to genres via taxonomy bridge
            genres = []
            for style in styles:
                for genre_entry in style_genres.get(style, ()):
                    if genre_entry not in genres:
                        genres.append(genre_entry)
                    all_genres.add((genre_entry["name"], genre_entry["slug"]))

            timeline.append({
                # discogs_id first: `id` is the table's AUTOINCREMENT rowid, which
                # means nothing outside this database. The old order read `id` ||
                # `discogs_id`, which is correct for releases_preview.json (where
                # `id` IS the Discogs id) but backwards for the schema — so the
                # timeline was emitting rowids. Consumers need the Discogs id to
                # resolve artwork and to link out.
                "id": r.get("discogs_id") or r.get("id"),
                "title": r.get("title", ""),
                "label": r.get("label", ""),
                "catno": r.get("catno", ""),
                "year": r.get("year", 0),
                "genres": genres,
                "youtube_url": r.get("youtube_url"),
                # Present when YOYAKU carries the record. `shop_url` leads to
                # the page that owns price and stock, so neither is copied here
                # where it would go stale between corpus rebuilds.
                "sku": r.get("sku"),
                "shop_url": r.get("shop_url"),
            })

        # Year range
        years = [t["year"] for t in timeline if t["year"]]

        return {
            "artist": name,
            "timeline": timeline,
            "total": len(timeline),
            # Additive, so no existing consumer changes: `total` still counts what
            # was returned. This says whether that is the whole story.
            "truncated": len(timeline) >= TIMELINE_MAX_RELEASES,
            "genres": [{"name": g[0], "slug": g[1]} for g in sorted(all_genres)],
            "year_min": min(years) if years else None,
            "year_max": max(years) if years else None,
        }
