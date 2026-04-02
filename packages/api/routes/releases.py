"""Release search endpoint — filter by style, country, year, label, text."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from ..db import get_db

# Load community stats if available
_community_stats = {}
_community_path = Path(__file__).parent.parent.parent.parent / "data" / "processed" / "community_stats.json"
if _community_path.exists():
    with open(_community_path) as f:
        _data = json.load(f)
        _community_stats = _data.get("stats", {})

router = APIRouter(prefix="/api/releases", tags=["releases"])


@router.get("")
def search_releases(
    genre: str | None = None,
    style: str | None = None,
    country: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    label: str | None = None,
    q: str | None = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0),
):
    """Search and filter releases from the Discogs dump."""
    try:
        with get_db() as conn:
            conditions = []
            params: list = []

            if style:
                conditions.append("styles LIKE ?")
                params.append(f'%"{style}"%')
            if country:
                conditions.append("country = ?")
                params.append(country)
            if year_min:
                conditions.append("year >= ?")
                params.append(year_min)
            if year_max:
                conditions.append("year <= ?")
                params.append(year_max)
            if label:
                conditions.append("label LIKE ?")
                params.append(f"%{label}%")
            if q:
                conditions.append("(title LIKE ? OR artist LIKE ?)")
                params.extend([f"%{q}%", f"%{q}%"])

            where = " AND ".join(conditions) if conditions else "1=1"

            # Count total matches
            count_params = list(params)
            total = conn.execute(
                f"SELECT COUNT(*) FROM releases WHERE {where}", count_params
            ).fetchone()[0]

            # Fetch page
            query = f"SELECT * FROM releases WHERE {where} ORDER BY year DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            releases = conn.execute(query, params).fetchall()

            # Enrich with community stats
            results = []
            for r in releases:
                row = dict(r)
                rid = str(row.get("id"))
                if rid in _community_stats:
                    row["community"] = _community_stats[rid]
                results.append(row)

            return {
                "releases": results,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
    except FileNotFoundError:
        raise HTTPException(
            503, "Database not available. Run build_db.py to generate it."
        )


@router.get("/community-rankings")
def community_rankings(
    sort: str = Query("wanted", pattern="^(wanted|owned|rated)$"),
    limit: int = Query(20, le=100),
):
    """Get releases ranked by community stats (most wanted/owned/highest rated)."""
    if not _community_stats:
        return {"rankings": [], "sort": sort, "total": 0}

    items = [(k, v) for k, v in _community_stats.items() if v is not None]

    if sort == "wanted":
        items.sort(key=lambda x: -x[1]["want"])
    elif sort == "owned":
        items.sort(key=lambda x: -x[1]["have"])
    elif sort == "rated":
        items = [(k, v) for k, v in items if v["rating_count"] >= 5]
        items.sort(key=lambda x: -x[1]["rating_average"])

    top = items[:limit]

    # Enrich with release info from DB
    try:
        with get_db() as conn:
            results = []
            for rid, stats in top:
                row = conn.execute(
                    "SELECT * FROM releases WHERE id = ?", (int(rid),)
                ).fetchone()
                if row:
                    r = dict(row)
                    r["community"] = stats
                    results.append(r)

            return {"rankings": results, "sort": sort, "total": len(_community_stats)}
    except FileNotFoundError:
        return {"rankings": [], "sort": sort, "total": 0}
