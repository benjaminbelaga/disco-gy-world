"""Record shop endpoints — real-world vinyl shops from OpenStreetMap."""

import json
import math
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/shops", tags=["shops"])

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_candidates = [
    Path(__file__).resolve().parent.parent.parent / "web" / "public" / "data" / "record_shops.json",
    Path("/var/www/world.yoyaku.io/data/record_shops.json"),
]
_SHOPS_JSON = next((p for p in _candidates if p.exists()), _candidates[0])

_shop_data: dict = {}
_shops: list[dict] = []


def _load_shops() -> None:
    global _shop_data, _shops
    if not _SHOPS_JSON.exists():
        return
    with open(_SHOPS_JSON) as f:
        _shop_data = json.load(f)
    _shops = _shop_data.get("shops", [])


_load_shops()


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
def list_shops(
    lat: float | None = None,
    lng: float | None = None,
    radius: float = Query(50, description="Radius in km (default 50)"),
    city: str | None = None,
    vinyl: bool | None = None,
    limit: int = Query(200, le=1000),
):
    """Search record shops by location or city name.

    - lat/lng + radius: shops within radius km of a point
    - city: case-insensitive city name search
    - vinyl: filter for vinyl/second-hand flagged shops
    """
    results = _shops

    if vinyl is not None and vinyl:
        results = [s for s in results if s.get("vinyl")]

    if city:
        city_lower = city.lower()
        results = [s for s in results if city_lower in s.get("city", "").lower()]
    elif lat is not None and lng is not None:
        results = [
            {**s, "_dist": _haversine_km(lat, lng, s["lat"], s["lng"])}
            for s in results
            if _haversine_km(lat, lng, s["lat"], s["lng"]) <= radius
        ]
        results.sort(key=lambda s: s["_dist"])
        # Remove internal distance field from output
        for s in results:
            s.pop("_dist", None)

    total = len(results)
    results = results[:limit]

    return {
        "meta": _shop_data.get("meta", {}),
        "total": total,
        "count": len(results),
        "shops": results,
    }
