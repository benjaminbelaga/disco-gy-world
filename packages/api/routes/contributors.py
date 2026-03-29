"""Contributor recognition — leaderboard, profiles, point system."""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..user_db import get_user_db

router = APIRouter(prefix="/api/contributors", tags=["contributors"])

# ---------------------------------------------------------------------------
# Point system
# ---------------------------------------------------------------------------

POINT_VALUES = {
    "genre_edit": 10,
    "path_created": 5,
    "youtube_link": 3,
    "data_enrichment": 5,
    "bug_report": 2,
}

VALID_TYPES = set(POINT_VALUES.keys())

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_CONTRIBUTORS_SCHEMA = """
CREATE TABLE IF NOT EXISTS contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    type TEXT NOT NULL,
    detail TEXT DEFAULT '',
    points INTEGER DEFAULT 1,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS contributor_profiles (
    username TEXT PRIMARY KEY,
    display_name TEXT,
    avatar_url TEXT,
    bio TEXT DEFAULT '',
    total_points INTEGER DEFAULT 0,
    joined_at REAL NOT NULL,
    last_active REAL
);

CREATE INDEX IF NOT EXISTS idx_contributions_user ON contributions(username);
CREATE INDEX IF NOT EXISTS idx_contributions_type ON contributions(type);
"""


def _ensure_tables():
    with get_user_db() as conn:
        conn.executescript(_CONTRIBUTORS_SCHEMA)
        conn.commit()


_ensure_tables()

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ContributeRequest(BaseModel):
    type: str
    detail: str = ""
    points: Optional[int] = None


class ContributionOut(BaseModel):
    id: int
    type: str
    detail: str
    points: int
    created_at: float


class ProfileOut(BaseModel):
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: str = ""
    total_points: int = 0
    joined_at: float
    last_active: Optional[float] = None


class LeaderboardEntry(BaseModel):
    username: str
    display_name: Optional[str] = None
    total_points: int
    contributions_count: int
    top_type: Optional[str] = None
    rank: int


class StatsOut(BaseModel):
    total_contributors: int
    total_contributions: int
    most_active_type: Optional[str] = None
    contributions_today: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_profile(conn, username: str) -> None:
    """Create a contributor profile if it doesn't exist yet."""
    row = conn.execute(
        "SELECT username FROM contributor_profiles WHERE username = ?",
        (username,),
    ).fetchone()
    if not row:
        now = time.time()
        conn.execute(
            "INSERT INTO contributor_profiles (username, display_name, total_points, joined_at, last_active) "
            "VALUES (?, ?, 0, ?, ?)",
            (username, username, now, now),
        )


def _period_filter(period: str, alias: str = "c") -> tuple[str, list]:
    """Return a SQL WHERE clause fragment and params for time filtering."""
    now = time.time()
    if period == "week":
        return f"AND {alias}.created_at >= ?", [now - 7 * 86400]
    elif period == "month":
        return f"AND {alias}.created_at >= ?", [now - 30 * 86400]
    return "", []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=StatsOut)
def contributor_stats():
    """Global contributor statistics."""
    with get_user_db() as conn:
        total_contributors = conn.execute(
            "SELECT COUNT(DISTINCT username) FROM contributions"
        ).fetchone()[0]

        total_contributions = conn.execute(
            "SELECT COUNT(*) FROM contributions"
        ).fetchone()[0]

        type_row = conn.execute(
            "SELECT type, COUNT(*) as cnt FROM contributions GROUP BY type ORDER BY cnt DESC LIMIT 1"
        ).fetchone()
        most_active_type = type_row[0] if type_row else None

        today_start = time.time() - 86400
        contributions_today = conn.execute(
            "SELECT COUNT(*) FROM contributions WHERE created_at >= ?",
            (today_start,),
        ).fetchone()[0]

    return StatsOut(
        total_contributors=total_contributors,
        total_contributions=total_contributions,
        most_active_type=most_active_type,
        contributions_today=contributions_today,
    )


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(
    period: str = Query("all", pattern="^(all|month|week)$"),
    limit: int = Query(20, ge=1, le=100),
):
    """Top contributors ranked by points."""
    period_clause, period_params = _period_filter(period, alias="c")
    period_clause_bare, period_params_bare = _period_filter(period, alias="contributions")

    with get_user_db() as conn:
        rows = conn.execute(
            f"""
            SELECT c.username,
                   p.display_name,
                   SUM(c.points) as total_points,
                   COUNT(*) as contributions_count
            FROM contributions c
            LEFT JOIN contributor_profiles p ON c.username = p.username
            WHERE 1=1 {period_clause}
            GROUP BY c.username
            ORDER BY total_points DESC
            LIMIT ?
            """,
            (*period_params, limit),
        ).fetchall()

        results = []
        for rank, row in enumerate(rows, 1):
            # Find top contribution type for this user
            top_type_row = conn.execute(
                f"""
                SELECT type, COUNT(*) as cnt
                FROM contributions
                WHERE username = ? {period_clause_bare}
                GROUP BY type ORDER BY cnt DESC LIMIT 1
                """,
                (row[0], *period_params_bare),
            ).fetchone()

            results.append(LeaderboardEntry(
                username=row[0],
                display_name=row[1],
                total_points=row[2],
                contributions_count=row[3],
                top_type=top_type_row[0] if top_type_row else None,
                rank=rank,
            ))

    return results


@router.get("/{username}")
def get_contributor(username: str):
    """Contributor profile with breakdown and recent activity."""
    with get_user_db() as conn:
        profile = conn.execute(
            "SELECT username, display_name, avatar_url, bio, total_points, joined_at, last_active "
            "FROM contributor_profiles WHERE username = ?",
            (username,),
        ).fetchone()

        if not profile:
            raise HTTPException(status_code=404, detail="Contributor not found")

        # Breakdown by type
        breakdown = conn.execute(
            "SELECT type, COUNT(*) as count, SUM(points) as points "
            "FROM contributions WHERE username = ? GROUP BY type",
            (username,),
        ).fetchall()

        # Recent activity
        recent = conn.execute(
            "SELECT id, type, detail, points, created_at "
            "FROM contributions WHERE username = ? ORDER BY created_at DESC LIMIT 20",
            (username,),
        ).fetchall()

    return {
        "profile": ProfileOut(
            username=profile[0],
            display_name=profile[1],
            avatar_url=profile[2],
            bio=profile[3] or "",
            total_points=profile[4],
            joined_at=profile[5],
            last_active=profile[6],
        ),
        "breakdown": [
            {"type": row[0], "count": row[1], "points": row[2]}
            for row in breakdown
        ],
        "recent": [
            ContributionOut(id=row[0], type=row[1], detail=row[2], points=row[3], created_at=row[4])
            for row in recent
        ],
    }


@router.post("/{username}/contribute")
def record_contribution(username: str, body: ContributeRequest):
    """Record a new contribution and update the profile."""
    if body.type not in VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type '{body.type}'. Must be one of: {', '.join(sorted(VALID_TYPES))}",
        )

    points = body.points if body.points is not None else POINT_VALUES.get(body.type, 1)
    now = time.time()

    with get_user_db() as conn:
        _ensure_profile(conn, username)

        conn.execute(
            "INSERT INTO contributions (username, type, detail, points, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, body.type, body.detail, points, now),
        )

        conn.execute(
            "UPDATE contributor_profiles SET total_points = total_points + ?, last_active = ? "
            "WHERE username = ?",
            (points, now, username),
        )
        conn.commit()

    return {"ok": True, "username": username, "type": body.type, "points": points}
