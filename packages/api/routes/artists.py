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
        total = conn.execute(
            "SELECT COUNT(*) FROM releases WHERE artist LIKE ?",
            (f"%{name}%",),
        ).fetchone()[0]

        rows = conn.execute(
            "SELECT * FROM releases WHERE artist LIKE ? ORDER BY year DESC LIMIT ? OFFSET ?",
            (f"%{name}%", limit, offset),
        ).fetchall()

        return {
            "artist": name,
            "releases": [dict(r) for r in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.get("/{name}/timeline")
def artist_timeline(name: str):
    """Releases sorted by year with genre mappings for timeline visualization."""
    if not db_available():
        raise HTTPException(503, "Database not available.")

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM releases WHERE artist LIKE ? AND year > 0 ORDER BY year ASC",
            (f"%{name}%",),
        ).fetchall()

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
                bridge_rows = conn.execute(
                    "SELECT g.name, g.slug FROM taxonomy_bridge tb "
                    "JOIN genres g ON tb.genre_id = g.id "
                    "WHERE tb.discogs_style = ?",
                    (style,),
                ).fetchall()
                for br in bridge_rows:
                    genre_entry = {"name": br[0], "slug": br[1]}
                    if genre_entry not in genres:
                        genres.append(genre_entry)
                    all_genres.add((br[0], br[1]))

            timeline.append({
                "id": r.get("id") or r.get("discogs_id"),
                "title": r.get("title", ""),
                "label": r.get("label", ""),
                "catno": r.get("catno", ""),
                "year": r.get("year", 0),
                "genres": genres,
                "youtube_url": r.get("youtube_url"),
            })

        # Year range
        years = [t["year"] for t in timeline if t["year"]]

        return {
            "artist": name,
            "timeline": timeline,
            "total": len(timeline),
            "genres": [{"name": g[0], "slug": g[1]} for g in sorted(all_genres)],
            "year_min": min(years) if years else None,
            "year_max": max(years) if years else None,
        }
