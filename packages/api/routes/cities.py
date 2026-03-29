"""City data endpoint — geographic data for the Earth Globe view."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/cities", tags=["cities"])

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_candidates = [
    Path(__file__).resolve().parent.parent.parent / "web" / "public" / "data" / "cities.json",
    Path("/var/www/world.yoyaku.io/data/cities.json"),
]
_CITIES_JSON = next((p for p in _candidates if p.exists()), _candidates[0])

_city_data: dict = {}
_cities_by_id: dict = {}


def _load_cities() -> None:
    global _city_data, _cities_by_id
    if not _CITIES_JSON.exists():
        return
    with open(_CITIES_JSON) as f:
        _city_data = json.load(f)
    _cities_by_id = {c["id"]: c for c in _city_data.get("cities", [])}


_load_cities()

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
def list_cities(
    country: str | None = None,
    genre: str | None = None,
    min_releases: int | None = None,
):
    """Return city list with coordinates and genre associations.

    Optional filters:
    - country: ISO country code or name
    - genre: filter cities that have this genre
    - min_releases: minimum release count threshold
    """
    cities = _city_data.get("cities", [])

    if country:
        country_lower = country.lower()
        cities = [c for c in cities if c["country"].lower() == country_lower]

    if genre:
        genre_lower = genre.lower()
        cities = [c for c in cities if genre_lower in [g.lower() for g in c["genres"]]]

    if min_releases is not None:
        cities = [c for c in cities if c.get("release_count", 0) >= min_releases]

    return {
        "meta": _city_data.get("meta", {}),
        "count": len(cities),
        "cities": cities,
    }


@router.get("/{city_id}")
def get_city(city_id: str):
    """Return a single city by ID."""
    city = _cities_by_id.get(city_id)
    if city is None:
        raise HTTPException(status_code=404, detail=f"City '{city_id}' not found")
    return city


@router.get("/{city_id}/artists")
def city_artists(
    city_id: str,
    limit: int = Query(50, le=500),
    offset: int = Query(0),
):
    """List top artists associated with a city.

    Returns artists from the enriched cities.json data.
    If the DB is available, also queries releases for additional artist matches.
    """
    city = _cities_by_id.get(city_id)
    if city is None:
        raise HTTPException(status_code=404, detail=f"City '{city_id}' not found")

    artists = city.get("artists", [])
    total = len(artists)
    paginated = artists[offset : offset + limit]

    result = {
        "city_id": city_id,
        "city_name": city["name"],
        "total": total,
        "artist_count": city.get("artist_count", total),
        "artists": paginated,
    }

    # If DB is available, enrich with release counts per artist
    try:
        from ..db import get_db, db_available

        if db_available() and paginated:
            with get_db() as conn:
                artist_stats = []
                for artist_name in paginated:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM releases WHERE artist = ?",
                        (artist_name,),
                    ).fetchone()[0]
                    artist_stats.append({
                        "name": artist_name,
                        "release_count": count,
                    })
                artist_stats.sort(key=lambda a: a["release_count"], reverse=True)
                result["artists"] = artist_stats
    except (ImportError, FileNotFoundError):
        pass  # DB not available — return plain artist list

    return result


@router.get("/{city_id}/labels")
def city_labels(
    city_id: str,
    limit: int = Query(50, le=500),
    offset: int = Query(0),
):
    """List top labels associated with a city.

    Returns labels from the enriched cities.json data.
    If the DB is available, also queries releases for additional label stats.
    """
    city = _cities_by_id.get(city_id)
    if city is None:
        raise HTTPException(status_code=404, detail=f"City '{city_id}' not found")

    labels = city.get("labels", [])
    total = len(labels)
    paginated = labels[offset : offset + limit]

    result = {
        "city_id": city_id,
        "city_name": city["name"],
        "total": total,
        "label_count": city.get("label_count", total),
        "labels": paginated,
    }

    # If DB is available, enrich with release counts per label
    try:
        from ..db import get_db, db_available

        if db_available() and paginated:
            with get_db() as conn:
                label_stats = []
                for label_name in paginated:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM releases WHERE label = ?",
                        (label_name,),
                    ).fetchone()[0]
                    label_stats.append({
                        "name": label_name,
                        "release_count": count,
                    })
                label_stats.sort(key=lambda a: a["release_count"], reverse=True)
                result["labels"] = label_stats
    except (ImportError, FileNotFoundError):
        pass  # DB not available — return plain label list

    return result
