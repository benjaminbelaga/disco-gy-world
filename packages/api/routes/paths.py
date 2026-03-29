"""Dig Paths — curated genre journeys that users can share."""

import json
import secrets
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..user_db import get_user_db

router = APIRouter(prefix="/api/paths", tags=["paths"])


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_PATHS_SCHEMA = """
CREATE TABLE IF NOT EXISTS dig_paths (
    id TEXT PRIMARY KEY,
    title TEXT DEFAULT '',
    description TEXT DEFAULT '',
    waypoints TEXT NOT NULL,
    created_at REAL NOT NULL,
    views INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_dig_paths_views ON dig_paths(views DESC);
CREATE INDEX IF NOT EXISTS idx_dig_paths_created ON dig_paths(created_at DESC);
"""


def _ensure_table():
    """Create the dig_paths table if it doesn't exist."""
    with get_user_db() as conn:
        conn.executescript(_PATHS_SCHEMA)
        conn.commit()


_ensure_table()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Waypoint(BaseModel):
    slug: str
    note: str = ""


class PathCreate(BaseModel):
    title: str = ""
    description: str = ""
    waypoints: list[Waypoint] = Field(..., min_length=1)


class PathResponse(BaseModel):
    id: str
    title: str
    description: str
    waypoints: list[Waypoint]
    created_at: float
    views: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def _generate_id() -> str:
    """Generate a short URL-safe ID (8 chars)."""
    return secrets.token_urlsafe(6)


@router.post("", response_model=PathResponse)
def create_path(body: PathCreate):
    """Save a curated dig path and return a short ID."""
    path_id = _generate_id()
    waypoints_json = json.dumps([w.model_dump() for w in body.waypoints])
    now = time.time()

    with get_user_db() as conn:
        conn.execute(
            "INSERT INTO dig_paths (id, title, description, waypoints, created_at, views) "
            "VALUES (?, ?, ?, ?, ?, 0)",
            (path_id, body.title, body.description, waypoints_json, now),
        )
        conn.commit()

    return PathResponse(
        id=path_id,
        title=body.title,
        description=body.description,
        waypoints=body.waypoints,
        created_at=now,
        views=0,
    )


@router.get("/popular", response_model=list[PathResponse])
def popular_paths(limit: int = 20):
    """Return the most-viewed dig paths."""
    with get_user_db() as conn:
        rows = conn.execute(
            "SELECT id, title, description, waypoints, created_at, views "
            "FROM dig_paths ORDER BY views DESC LIMIT ?",
            (min(limit, 50),),
        ).fetchall()

    return [
        PathResponse(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            waypoints=json.loads(row["waypoints"]),
            created_at=row["created_at"],
            views=row["views"],
        )
        for row in rows
    ]


@router.get("/{path_id}", response_model=PathResponse)
def get_path(path_id: str):
    """Retrieve a dig path by ID and increment its view count."""
    with get_user_db() as conn:
        row = conn.execute(
            "SELECT id, title, description, waypoints, created_at, views "
            "FROM dig_paths WHERE id = ?",
            (path_id,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Path not found")

        # Bump view count
        conn.execute(
            "UPDATE dig_paths SET views = views + 1 WHERE id = ?",
            (path_id,),
        )
        conn.commit()

    return PathResponse(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        waypoints=json.loads(row["waypoints"]),
        created_at=row["created_at"],
        views=row["views"] + 1,
    )
