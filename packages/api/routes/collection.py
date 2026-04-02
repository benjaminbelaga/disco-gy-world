"""User collection routes — sync, browse, wantlist, taste stats."""

import json
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from ..discogs_client import fetch_all_collection, fetch_all_wantlist
from ..user_db import get_user_db
from .auth import _lookup_session

router = APIRouter(prefix="/api/collection", tags=["collection"])


def _get_user_from_session(session_token: str | None) -> dict:
    """Validate session and return user info."""
    user = _lookup_session(session_token)
    if not user:
        raise HTTPException(401, "Not authenticated. Provide a valid session_token.")
    return user


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


@router.get("/sync")
def sync_collection(session_token: str = Query(...)):
    """Fetch user's Discogs collection + wantlist and store locally.

    This calls the Discogs API (rate-limited to 60 req/min) and may take
    a few seconds for large collections.
    """
    session = _get_user_from_session(session_token)
    user_id = session["user_id"]
    username = session["discogs_username"]

    # Get user's token from DB
    with get_user_db() as conn:
        user = conn.execute(
            "SELECT access_token FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            raise HTTPException(404, "User not found")
        token = user["access_token"]

    # Fetch collection from Discogs
    try:
        releases = fetch_all_collection(username, token=token)
    except Exception as e:
        raise HTTPException(502, f"Discogs API error (collection): {e}")

    # Fetch wantlist
    try:
        wants = fetch_all_wantlist(username, token=token)
    except Exception as e:
        raise HTTPException(502, f"Discogs API error (wantlist): {e}")

    # Store in DB
    now = datetime.utcnow().isoformat()
    with get_user_db() as conn:
        # Clear old data for this user
        conn.execute("DELETE FROM user_collection WHERE user_id = ?", (user_id,))

        # Insert collection
        for rel in releases:
            basic = rel.get("basic_information", {})
            discogs_id = rel.get("id") or basic.get("id", 0)
            rating = rel.get("rating", 0)
            date_added = rel.get("date_added", "")
            conn.execute(
                """INSERT OR REPLACE INTO user_collection
                   (user_id, release_id, discogs_release_id, rating, date_added, source)
                   VALUES (?, ?, ?, ?, ?, 'collection')""",
                (user_id, basic.get("id", 0), discogs_id, rating, date_added),
            )

        # Insert wantlist
        for want in wants:
            basic = want.get("basic_information", {})
            discogs_id = want.get("id") or basic.get("id", 0)
            rating = want.get("rating", 0)
            date_added = want.get("date_added", "")
            conn.execute(
                """INSERT OR REPLACE INTO user_collection
                   (user_id, release_id, discogs_release_id, rating, date_added, source)
                   VALUES (?, ?, ?, ?, ?, 'wantlist')""",
                (user_id, basic.get("id", 0), discogs_id, rating, date_added),
            )

        # Update synced_at
        conn.execute(
            "UPDATE users SET synced_at = ? WHERE id = ?", (now, user_id)
        )
        conn.commit()

    return {
        "status": "ok",
        "synced_at": now,
        "collection_count": len(releases),
        "wantlist_count": len(wants),
    }


# ---------------------------------------------------------------------------
# Browse
# ---------------------------------------------------------------------------


@router.get("")
def get_collection(
    session_token: str = Query(...),
    source: str = Query("collection", description="'collection' or 'wantlist'"),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
):
    """Return user's synced collection from local DB."""
    session = _get_user_from_session(session_token)
    user_id = session["user_id"]

    with get_user_db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM user_collection WHERE user_id = ? AND source = ?",
            (user_id, source),
        ).fetchone()[0]

        rows = conn.execute(
            """SELECT uc.discogs_release_id, uc.rating, uc.date_added, uc.source,
                      r.title, r.artist, r.label, r.year, r.styles, r.country
               FROM user_collection uc
               LEFT JOIN releases r ON r.discogs_id = uc.discogs_release_id
               WHERE uc.user_id = ? AND uc.source = ?
               ORDER BY uc.date_added DESC
               LIMIT ? OFFSET ?""",
            (user_id, source, limit, offset),
        ).fetchall()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "releases": [
            {
                "discogs_release_id": r["discogs_release_id"],
                "rating": r["rating"],
                "date_added": r["date_added"],
                "source": r["source"],
                "title": r["title"],
                "artist": r["artist"],
                "label": r["label"],
                "year": r["year"],
                "styles": r["styles"],
                "country": r["country"],
            }
            for r in rows
        ],
    }


@router.get("/wantlist")
def get_wantlist(
    session_token: str = Query(...),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
):
    """Return user's wantlist from local DB."""
    session = _get_user_from_session(session_token)
    user_id = session["user_id"]

    with get_user_db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM user_collection WHERE user_id = ? AND source = 'wantlist'",
            (user_id,),
        ).fetchone()[0]

        rows = conn.execute(
            """SELECT uc.discogs_release_id, uc.rating, uc.date_added,
                      r.title, r.artist, r.label, r.year, r.styles, r.country
               FROM user_collection uc
               LEFT JOIN releases r ON r.discogs_id = uc.discogs_release_id
               WHERE uc.user_id = ? AND uc.source = 'wantlist'
               ORDER BY uc.date_added DESC
               LIMIT ? OFFSET ?""",
            (user_id, limit, offset),
        ).fetchall()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "releases": [
            {
                "discogs_release_id": r["discogs_release_id"],
                "rating": r["rating"],
                "date_added": r["date_added"],
                "title": r["title"],
                "artist": r["artist"],
                "label": r["label"],
                "year": r["year"],
                "styles": r["styles"],
                "country": r["country"],
            }
            for r in rows
        ],
    }


# ---------------------------------------------------------------------------
# Stats — taste profile
# ---------------------------------------------------------------------------


@router.get("/stats")
def collection_stats(session_token: str = Query(...)):
    """Taste profile stats: genre distribution, decade spread, rarity score, top labels."""
    session = _get_user_from_session(session_token)
    user_id = session["user_id"]

    with get_user_db() as conn:
        rows = conn.execute(
            """SELECT uc.discogs_release_id, uc.rating, uc.source,
                      r.styles, r.year, r.label, r.country
               FROM user_collection uc
               LEFT JOIN releases r ON r.discogs_id = uc.discogs_release_id
               WHERE uc.user_id = ?""",
            (user_id,),
        ).fetchall()

    if not rows:
        return {
            "total_items": 0,
            "collection_count": 0,
            "wantlist_count": 0,
            "genre_distribution": {},
            "decade_distribution": {},
            "top_labels": [],
            "top_countries": [],
            "average_rating": 0,
            "rarity_score": 0,
        }

    style_counter: Counter = Counter()
    decade_counter: Counter = Counter()
    label_counter: Counter = Counter()
    country_counter: Counter = Counter()
    ratings: list[int] = []
    collection_count = 0
    wantlist_count = 0
    matched_in_db = 0

    for row in rows:
        if row["source"] == "collection":
            collection_count += 1
        else:
            wantlist_count += 1

        if row["rating"] and row["rating"] > 0:
            ratings.append(row["rating"])

        # Parse styles (JSON array stored as text)
        if row["styles"]:
            matched_in_db += 1
            try:
                styles = json.loads(row["styles"]) if isinstance(row["styles"], str) else []
            except (json.JSONDecodeError, TypeError):
                styles = [s.strip() for s in str(row["styles"]).split(",") if s.strip()]
            for style in styles:
                style_counter[style] += 1

        if row["year"]:
            decade = (row["year"] // 10) * 10
            decade_counter[f"{decade}s"] += 1

        if row["label"]:
            label_counter[row["label"]] += 1

        if row["country"]:
            country_counter[row["country"]] += 1

    total = len(rows)
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0

    # Rarity score: % of collection NOT matched in our DB (= obscure releases)
    rarity_score = round((1 - matched_in_db / total) * 100, 1) if total > 0 else 0

    return {
        "total_items": total,
        "collection_count": collection_count,
        "wantlist_count": wantlist_count,
        "genre_distribution": dict(style_counter.most_common(30)),
        "decade_distribution": dict(sorted(decade_counter.items())),
        "top_labels": [{"name": k, "count": v} for k, v in label_counter.most_common(20)],
        "top_countries": [{"name": k, "count": v} for k, v in country_counter.most_common(15)],
        "average_rating": avg_rating,
        "rarity_score": rarity_score,
    }
