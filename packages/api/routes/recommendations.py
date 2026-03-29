"""Recommendation endpoint — content-based release neighbors."""

from fastapi import APIRouter, HTTPException, Query

from ..db import get_db

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("/{release_id}")
def get_recommendations(release_id: int, limit: int = Query(10, le=50)):
    """Get similar releases based on pre-computed content similarity."""
    try:
        with get_db() as conn:
            release = conn.execute(
                "SELECT * FROM releases WHERE id = ? OR discogs_id = ?",
                (release_id, release_id),
            ).fetchone()
            if not release:
                raise HTTPException(404, "Release not found")

            neighbors = conn.execute(
                "SELECT r.*, rn.score FROM release_neighbors rn "
                "JOIN releases r ON r.id = rn.neighbor_id "
                "WHERE rn.release_id = ? ORDER BY rn.score DESC LIMIT ?",
                (release["id"], limit),
            ).fetchall()

            return {
                "release": dict(release),
                "recommendations": [dict(n) for n in neighbors],
            }
    except FileNotFoundError:
        raise HTTPException(
            503, "Database not available. Run build_db.py to generate it."
        )
