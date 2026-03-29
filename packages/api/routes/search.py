"""Unified search endpoint -- genres, artists, labels with fuzzy matching."""

import json
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..db import get_db, db_available

router = APIRouter(prefix="/api", tags=["search"])

# In-memory genre data (set by main.py on startup)
_genres: list = []
_genres_by_slug: dict = {}


def init_search_genres(genres: list, genres_by_slug: dict) -> None:
    """Called from main.py after loading world.json."""
    global _genres, _genres_by_slug
    _genres = genres
    _genres_by_slug = genres_by_slug


def _fuzzy_score(query: str, text: str) -> float:
    """Simple fuzzy scoring: exact > starts-with > contains > trigram overlap."""
    q = query.lower()
    t = text.lower()

    if q == t:
        return 100.0
    if t.startswith(q):
        return 80.0 + (len(q) / max(len(t), 1)) * 10
    if q in t:
        return 50.0 + (len(q) / max(len(t), 1)) * 20

    # Trigram overlap for typo tolerance
    q_tri = {q[i:i+3] for i in range(len(q) - 2)} if len(q) >= 3 else {q}
    t_tri = {t[i:i+3] for i in range(len(t) - 2)} if len(t) >= 3 else {t}
    if not q_tri:
        return 0.0
    overlap = len(q_tri & t_tri) / len(q_tri)
    return overlap * 40 if overlap > 0.3 else 0.0


def _search_genres(query: str, limit: int) -> list:
    """Search genres from in-memory world.json data."""
    results = []
    for g in _genres:
        searchable_parts = [g["name"]]
        if g.get("scene"):
            searchable_parts.append(g["scene"])
        if g.get("aka"):
            searchable_parts.extend(a.strip() for a in g["aka"].split(","))

        best_score = 0.0
        for part in searchable_parts:
            score = _fuzzy_score(query, part)
            best_score = max(best_score, score)

        if best_score > 0:
            results.append({
                "name": g["name"],
                "slug": g["slug"],
                "scene": g.get("scene", ""),
                "color": g.get("color", "#ffffff"),
                "x": g.get("x", 0),
                "y": g.get("y", 0),
                "z": g.get("z", 0),
                "size": g.get("size", 1),
                "score": round(best_score, 1),
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def _search_artists(query: str, limit: int) -> list:
    """Search distinct artists from SQLite releases table."""
    if not db_available():
        return []

    with get_db() as conn:
        # Use LIKE for prefix + contains matching, deduplicate
        rows = conn.execute(
            """
            SELECT artist, COUNT(*) as release_count
            FROM releases
            WHERE artist LIKE ? AND artist IS NOT NULL AND artist != ''
            GROUP BY artist
            ORDER BY
                CASE
                    WHEN LOWER(artist) = LOWER(?) THEN 0
                    WHEN LOWER(artist) LIKE LOWER(? || '%') THEN 1
                    ELSE 2
                END,
                release_count DESC
            LIMIT ?
            """,
            (f"%{query}%", query, query, limit * 3),
        ).fetchall()

        results = []
        for row in rows:
            score = _fuzzy_score(query, row["artist"])
            if score > 0:
                results.append({
                    "name": row["artist"],
                    "release_count": row["release_count"],
                    "score": round(score, 1),
                })

        results.sort(key=lambda r: (r["score"], r["release_count"]), reverse=True)
        return results[:limit]


def _search_labels(query: str, limit: int) -> list:
    """Search distinct labels from SQLite releases table."""
    if not db_available():
        return []

    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT label, COUNT(*) as release_count
            FROM releases
            WHERE label LIKE ? AND label IS NOT NULL AND label != ''
            GROUP BY label
            ORDER BY
                CASE
                    WHEN LOWER(label) = LOWER(?) THEN 0
                    WHEN LOWER(label) LIKE LOWER(? || '%') THEN 1
                    ELSE 2
                END,
                release_count DESC
            LIMIT ?
            """,
            (f"%{query}%", query, query, limit * 3),
        ).fetchall()

        results = []
        for row in rows:
            score = _fuzzy_score(query, row["label"])
            if score > 0:
                results.append({
                    "name": row["label"],
                    "release_count": row["release_count"],
                    "score": round(score, 1),
                })

        results.sort(key=lambda r: (r["score"], r["release_count"]), reverse=True)
        return results[:limit]


@router.get("/search/unified")
def unified_search(
    q: Optional[str] = Query(None, min_length=1),
    limit: int = Query(8, ge=1, le=50),
):
    """Fuzzy search across genres, artists, and labels. Returns grouped results."""
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    q_clean = q.strip()
    if len(q_clean) < 1:
        return {"query": q, "genres": [], "artists": [], "labels": []}

    genres = _search_genres(q_clean, limit)
    artists = _search_artists(q_clean, limit)
    labels = _search_labels(q_clean, limit)

    return {
        "query": q,
        "genres": genres,
        "artists": artists,
        "labels": labels,
    }
