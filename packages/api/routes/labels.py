"""Label endpoints — releases by label, genres where a label is present."""

from fastapi import APIRouter, HTTPException, Query

from ..db import get_db, db_available

router = APIRouter(prefix="/api/labels", tags=["labels"])


@router.get("/{name}/releases")
def label_releases(
    name: str,
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """All releases from a given label (case-insensitive substring match)."""
    if not db_available():
        raise HTTPException(503, "Database not available.")

    with get_db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM releases WHERE label LIKE ?",
            (f"%{name}%",),
        ).fetchone()[0]

        rows = conn.execute(
            "SELECT * FROM releases WHERE label LIKE ? ORDER BY year DESC LIMIT ? OFFSET ?",
            (f"%{name}%", limit, offset),
        ).fetchall()

        return {
            "label": name,
            "releases": [dict(r) for r in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.get("/{name}/genres")
def label_genres(name: str):
    """Genres where this label has releases (via taxonomy bridge or style matching)."""
    if not db_available():
        raise HTTPException(503, "Database not available.")

    with get_db() as conn:
        # Get distinct styles from this label's releases
        rows = conn.execute(
            "SELECT DISTINCT styles FROM releases WHERE label LIKE ?",
            (f"%{name}%",),
        ).fetchall()

        import json

        style_set = set()
        for row in rows:
            try:
                styles = json.loads(row[0]) if row[0] else []
                for s in styles:
                    style_set.add(s)
            except (json.JSONDecodeError, TypeError):
                pass

        # Map styles to genres via taxonomy bridge
        genres = set()
        for style in style_set:
            bridge_rows = conn.execute(
                "SELECT g.name, g.slug FROM taxonomy_bridge tb "
                "JOIN genres g ON tb.genre_id = g.id "
                "WHERE tb.discogs_style = ?",
                (style,),
            ).fetchall()
            for br in bridge_rows:
                genres.add((br[0], br[1]))

        # Year range and release count
        stats = conn.execute(
            "SELECT COUNT(*), MIN(year), MAX(year) FROM releases WHERE label LIKE ? AND year > 0",
            (f"%{name}%",),
        ).fetchone()

        return {
            "label": name,
            "genres": [{"name": g[0], "slug": g[1]} for g in sorted(genres)],
            "release_count": stats[0] if stats else 0,
            "year_min": stats[1] if stats else None,
            "year_max": stats[2] if stats else None,
        }
