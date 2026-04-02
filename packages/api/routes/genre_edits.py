"""Community genre editing — propose, vote, and review genre metadata changes."""

import json
import time

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..user_db import get_user_db

router = APIRouter(prefix="/api/genre-edits", tags=["genre-edits"])

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS genre_edits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genre_slug TEXT NOT NULL,
    field TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    reason TEXT DEFAULT '',
    author TEXT DEFAULT 'anonymous',
    status TEXT DEFAULT 'pending',
    created_at REAL NOT NULL,
    reviewed_at REAL,
    reviewed_by TEXT
);

CREATE TABLE IF NOT EXISTS genre_edit_votes (
    edit_id INTEGER REFERENCES genre_edits(id),
    voter TEXT NOT NULL,
    vote TEXT NOT NULL,
    created_at REAL NOT NULL,
    PRIMARY KEY (edit_id, voter)
);

CREATE INDEX IF NOT EXISTS idx_genre_edits_status ON genre_edits(status);
CREATE INDEX IF NOT EXISTS idx_genre_edits_slug ON genre_edits(genre_slug);
"""

VALID_FIELDS = {'description', 'aka', 'scene', 'biome', 'emerged'}
APPROVAL_THRESHOLD = 3
REJECTION_THRESHOLD = 3


def _ensure_tables():
    with get_user_db() as conn:
        conn.executescript(_SCHEMA)
        conn.commit()


_ensure_tables()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class EditProposal(BaseModel):
    genre_slug: str
    field: str
    new_value: str
    reason: str = ""
    author: str = "anonymous"


class VoteRequest(BaseModel):
    vote: str = Field(..., pattern="^(approve|reject)$")
    voter: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("")
def create_edit(body: EditProposal):
    """Submit a genre edit proposal."""
    if body.field not in VALID_FIELDS:
        raise HTTPException(422, f"Invalid field '{body.field}'. Valid: {', '.join(sorted(VALID_FIELDS))}")

    with get_user_db() as conn:
        now = time.time()
        cursor = conn.execute(
            """INSERT INTO genre_edits (genre_slug, field, new_value, reason, author, status, created_at)
               VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
            (body.genre_slug, body.field, body.new_value, body.reason, body.author, now),
        )
        conn.commit()
        edit_id = cursor.lastrowid

    return {
        "id": edit_id,
        "genre_slug": body.genre_slug,
        "field": body.field,
        "new_value": body.new_value,
        "reason": body.reason,
        "author": body.author,
        "status": "pending",
        "created_at": now,
    }


@router.get("")
def list_edits(
    status: str = Query(None),
    genre_slug: str = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """List edit proposals with optional filters."""
    conditions = []
    params = []

    if status:
        conditions.append("status = ?")
        params.append(status)
    if genre_slug:
        conditions.append("genre_slug = ?")
        params.append(genre_slug)

    where = " AND ".join(conditions) if conditions else "1=1"

    with get_user_db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM genre_edits WHERE {where}", params
        ).fetchone()[0]

        rows = conn.execute(
            f"SELECT * FROM genre_edits WHERE {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

    return {
        "edits": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
def edit_stats():
    """Community editing stats."""
    with get_user_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM genre_edits").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM genre_edits WHERE status = 'pending'").fetchone()[0]
        approved = conn.execute("SELECT COUNT(*) FROM genre_edits WHERE status = 'approved'").fetchone()[0]
        rejected = conn.execute("SELECT COUNT(*) FROM genre_edits WHERE status = 'rejected'").fetchone()[0]

        top_contributors = conn.execute(
            """SELECT author, COUNT(*) as edit_count
               FROM genre_edits
               GROUP BY author
               ORDER BY edit_count DESC
               LIMIT 10"""
        ).fetchall()

        top_genres = conn.execute(
            """SELECT genre_slug, COUNT(*) as edit_count
               FROM genre_edits
               GROUP BY genre_slug
               ORDER BY edit_count DESC
               LIMIT 10"""
        ).fetchall()

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "top_contributors": [{"author": r[0], "count": r[1]} for r in top_contributors],
        "top_genres": [{"slug": r[0], "count": r[1]} for r in top_genres],
    }


@router.get("/{edit_id}")
def get_edit(edit_id: int):
    """Get a single edit proposal with votes."""
    with get_user_db() as conn:
        edit = conn.execute("SELECT * FROM genre_edits WHERE id = ?", (edit_id,)).fetchone()
        if not edit:
            raise HTTPException(404, "Edit not found")

        votes = conn.execute(
            "SELECT voter, vote, created_at FROM genre_edit_votes WHERE edit_id = ?",
            (edit_id,),
        ).fetchall()

    return {
        **dict(edit),
        "votes": [{"voter": v[0], "vote": v[1], "created_at": v[2]} for v in votes],
        "approve_count": sum(1 for v in votes if v[1] == "approve"),
        "reject_count": sum(1 for v in votes if v[1] == "reject"),
    }


@router.post("/{edit_id}/vote")
def vote_on_edit(edit_id: int, body: VoteRequest):
    """Vote on a genre edit proposal."""
    with get_user_db() as conn:
        edit = conn.execute("SELECT * FROM genre_edits WHERE id = ?", (edit_id,)).fetchone()
        if not edit:
            raise HTTPException(404, "Edit not found")
        if edit["status"] != "pending":
            raise HTTPException(400, f"Edit already {edit['status']}")

        # Check for duplicate vote
        existing = conn.execute(
            "SELECT vote FROM genre_edit_votes WHERE edit_id = ? AND voter = ?",
            (edit_id, body.voter),
        ).fetchone()
        if existing:
            raise HTTPException(409, f"Already voted: {existing[0]}")

        # Record vote
        now = time.time()
        conn.execute(
            "INSERT INTO genre_edit_votes (edit_id, voter, vote, created_at) VALUES (?, ?, ?, ?)",
            (edit_id, body.voter, body.vote, now),
        )

        # Check thresholds
        approvals = conn.execute(
            "SELECT COUNT(*) FROM genre_edit_votes WHERE edit_id = ? AND vote = 'approve'",
            (edit_id,),
        ).fetchone()[0]
        rejections = conn.execute(
            "SELECT COUNT(*) FROM genre_edit_votes WHERE edit_id = ? AND vote = 'reject'",
            (edit_id,),
        ).fetchone()[0]

        new_status = "pending"
        if approvals >= APPROVAL_THRESHOLD:
            new_status = "approved"
            conn.execute(
                "UPDATE genre_edits SET status = 'approved', reviewed_at = ? WHERE id = ?",
                (now, edit_id),
            )
        elif rejections >= REJECTION_THRESHOLD:
            new_status = "rejected"
            conn.execute(
                "UPDATE genre_edits SET status = 'rejected', reviewed_at = ? WHERE id = ?",
                (now, edit_id),
            )

        conn.commit()

    return {
        "edit_id": edit_id,
        "vote": body.vote,
        "voter": body.voter,
        "approve_count": approvals,
        "reject_count": rejections,
        "status": new_status,
    }
