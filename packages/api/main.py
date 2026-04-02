"""DiscoWorld API — genre data, search, and stats."""

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .routes.artists import router as artists_router
from .routes.auth import router as auth_router
from .routes.cities import router as cities_router
from .routes.collection import router as collection_router
from .routes.labels import router as labels_router
from .routes.paths import router as paths_router
from .routes.personal_reco import router as personal_reco_router
from .routes.recommendations import router as recommendations_router
from .routes.releases import router as releases_router
from .routes.crate_neighbors import router as crate_neighbors_router
from .routes.search import router as search_router
from .routes.search import init_search_genres
from .routes.shops import router as shops_router
from .routes.taste_profile import router as taste_profile_router
from .routes.contributors import router as contributors_router
from .routes.genre_edits import router as genre_edits_router
from .user_db import init_user_db

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

import os

# Try multiple paths
_candidates = [
    Path(__file__).resolve().parent / "data" / "world.json",
    Path(__file__).resolve().parent.parent / "web" / "public" / "data" / "world.json",
]
WORLD_JSON = next((p for p in _candidates if p.exists()), _candidates[1])

_data: dict = {}
_genres_by_slug: dict = {}


def _load_data() -> None:
    global _data, _genres_by_slug
    with open(WORLD_JSON) as f:
        _data = json.load(f)
    _genres_by_slug = {g["slug"]: g for g in _data["genres"]}


_load_data()

# Initialize search module with genre data
init_search_genres(_data.get("genres", []), _genres_by_slug)

# Initialize user database tables
init_user_db()

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="DiscoWorld API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("DISCOWORLD_ORIGIN", "http://localhost:5173"),
        "http://localhost:5173",
        "http://localhost:4173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# SQLite-backed routes (releases, recommendations, auth, collection)
app.include_router(artists_router)
app.include_router(auth_router)
app.include_router(cities_router)
app.include_router(collection_router)
app.include_router(labels_router)
app.include_router(paths_router)
app.include_router(personal_reco_router)
app.include_router(recommendations_router)
app.include_router(releases_router)
app.include_router(crate_neighbors_router)
app.include_router(search_router)
app.include_router(shops_router)
app.include_router(taste_profile_router)
app.include_router(contributors_router)
app.include_router(genre_edits_router)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health():
    return {"status": "ok", "genres": len(_genres_by_slug)}


@app.get("/api/genres")
def list_genres():
    """Return all genres (without tracks for lighter payload)."""
    return {
        "meta": _data["meta"],
        "genres": _data["genres"],
    }


@app.get("/api/genres/{slug}")
def get_genre(slug: str):
    """Return a single genre with its tracks."""
    genre = _genres_by_slug.get(slug)
    if genre is None:
        raise HTTPException(status_code=404, detail=f"Genre '{slug}' not found")

    tracks = _data.get("tracks", {}).get(slug, [])
    return {**genre, "tracks": tracks}


@app.get("/api/search")
def search_genres(q: Optional[str] = Query(None, min_length=1)):
    """Search genres by name, scene, or aka. Case-insensitive substring match."""
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    q_lower = q.lower()
    results = []
    for g in _data["genres"]:
        searchable = f"{g['name']} {g.get('scene', '')} {g.get('aka', '')}".lower()
        if q_lower in searchable:
            results.append(g)

    return {"query": q, "count": len(results), "genres": results}


@app.get("/api/stats")
def stats():
    """Return meta stats about the dataset."""
    meta = _data["meta"]
    scenes = set()
    biomes = set()
    for g in _data["genres"]:
        if g.get("scene"):
            scenes.add(g["scene"])
        if g.get("biome"):
            biomes.add(g["biome"])

    return {
        **meta,
        "sceneCount": len(scenes),
        "biomeCount": len(biomes),
        "scenes": sorted(scenes),
        "biomes": sorted(biomes),
    }
