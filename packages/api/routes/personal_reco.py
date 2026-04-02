"""Personal recommendation engine — Phase 2 of DiscoWorld discovery.

Uses Phase 0 content-based neighbors + user's Discogs collection to generate
personalized recommendations. Works WITHOUT OAuth: accepts ?discogs_username=xxx
and fetches the user's PUBLIC collection via Discogs API.
"""

import logging
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from ..db import get_db
from ..discogs_client import fetch_all_collection, fetch_all_wantlist
from ..user_db import get_user_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recommendations", tags=["personal"])

# In-memory cooldown to avoid re-fetching within same session
_sync_timestamps: dict[str, float] = {}
SYNC_COOLDOWN = 3600  # 1 hour


def _sync_public_collection(username: str) -> dict:
    """Fetch a Discogs user's public collection+wantlist and store in user_db.

    No token needed — Discogs public collections are accessible without auth
    (at 25 req/min instead of 60, but our rate limiter handles this).
    """
    now = datetime.utcnow().isoformat()

    # Fetch from Discogs API (uses existing rate-limited client)
    try:
        releases = fetch_all_collection(username, token=None)
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(404, f"Discogs user '{username}' not found")
        if "403" in str(e):
            raise HTTPException(403, f"Collection for '{username}' is private")
        raise HTTPException(502, f"Discogs API error: {e}")

    try:
        wants = fetch_all_wantlist(username, token=None)
    except Exception:
        wants = []  # Wantlist may be private; not fatal

    # Ensure user exists in user_db
    with get_user_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE discogs_username = ?", (username,)
        ).fetchone()

        if existing:
            user_id = existing["id"]
        else:
            cursor = conn.execute(
                "INSERT INTO users (discogs_username) VALUES (?)", (username,)
            )
            user_id = cursor.lastrowid
            conn.commit()

        # Clear previous sync
        conn.execute("DELETE FROM user_collection WHERE user_id = ?", (user_id,))

        # Store collection
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

        # Store wantlist
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

    _sync_timestamps[username] = time.time()

    return {
        "user_id": user_id,
        "collection_count": len(releases),
        "wantlist_count": len(wants),
    }


@router.get("/personal")
def personal_recommendations(
    discogs_username: str = Query(..., description="Discogs username (public collection)"),
    hidden_gems: bool = Query(False, description="Filter for releases with low community ownership"),
    limit: int = Query(50, le=100),
    refresh: bool = Query(False, description="Force re-sync from Discogs"),
):
    """Personalized recommendations based on a user's Discogs collection.

    Works WITHOUT Discogs OAuth — fetches public collection by username.

    Algorithm:
    1. Fetch user's collection from Discogs (cached, refresh on demand)
    2. Match collection releases to our DB via discogs_id
    3. For each matched release, look up pre-computed neighbors (release_neighbors)
    4. Aggregate neighbor scores across all owned releases, weighted by rating
    5. Exclude releases already in collection or wantlist
    6. Sort by aggregate score descending, return top N
    """
    # Sync if needed
    cache_ts = _sync_timestamps.get(discogs_username, 0)
    needs_sync = refresh or (time.time() - cache_ts) > SYNC_COOLDOWN

    # Check if user has data
    with get_user_db() as uconn:
        user = uconn.execute(
            "SELECT id, synced_at FROM users WHERE discogs_username = ?",
            (discogs_username,),
        ).fetchone()
        if not user or not user["synced_at"]:
            needs_sync = True

    if needs_sync:
        sync_result = _sync_public_collection(discogs_username)
        with get_user_db() as uconn:
            user = uconn.execute(
                "SELECT id FROM users WHERE discogs_username = ?",
                (discogs_username,),
            ).fetchone()

    if not user:
        raise HTTPException(404, f"User '{discogs_username}' not found after sync")

    user_id = user["id"]

    # Get user's collection discogs_release_ids and match to main DB
    with get_user_db() as uconn:
        coll_rows = uconn.execute(
            "SELECT discogs_release_id, rating, source FROM user_collection WHERE user_id = ?",
            (user_id,),
        ).fetchall()

    if not coll_rows:
        return {
            "username": discogs_username,
            "collection_matched": 0,
            "wantlist_matched": 0,
            "recommendations": [],
            "message": "No releases found in collection. Is the collection public?",
        }

    # Split by source
    collection_discogs_ids = {}
    wantlist_discogs_ids = set()
    for row in coll_rows:
        if row["source"] == "collection":
            collection_discogs_ids[row["discogs_release_id"]] = row["rating"] or 0
        else:
            wantlist_discogs_ids.add(row["discogs_release_id"])

    # Match to main discoworld.db
    try:
        with get_db() as conn:
            # Find internal IDs for user's collection releases
            all_discogs_ids = list(collection_discogs_ids.keys()) + list(wantlist_discogs_ids)
            if not all_discogs_ids:
                return {
                    "username": discogs_username,
                    "collection_matched": 0,
                    "wantlist_matched": 0,
                    "recommendations": [],
                }

            placeholders = ",".join("?" * len(all_discogs_ids))
            matched_rows = conn.execute(
                f"SELECT id, discogs_id FROM releases WHERE discogs_id IN ({placeholders})",
                all_discogs_ids,
            ).fetchall()

            # Build mapping: discogs_id -> internal_id
            discogs_to_internal = {r["discogs_id"]: r["id"] for r in matched_rows}

            # Owned internal IDs (collection items with rating weights)
            owned_items = []
            for discogs_id, rating in collection_discogs_ids.items():
                internal_id = discogs_to_internal.get(discogs_id)
                if internal_id:
                    owned_items.append((internal_id, max(rating, 1)))

            # All excluded IDs (owned + wantlisted)
            excluded_ids = set()
            for discogs_id in list(collection_discogs_ids.keys()) + list(wantlist_discogs_ids):
                internal_id = discogs_to_internal.get(discogs_id)
                if internal_id:
                    excluded_ids.add(internal_id)

            if not owned_items:
                return {
                    "username": discogs_username,
                    "collection_matched": 0,
                    "wantlist_matched": len(
                        [d for d in wantlist_discogs_ids if d in discogs_to_internal]
                    ),
                    "recommendations": [],
                    "message": "No collection releases matched our database. "
                    "We currently index vinyl electronic releases only.",
                }

            # Aggregate neighbor scores across all owned releases
            # For each owned release, get its neighbors and sum weighted scores
            score_map: dict[int, float] = {}
            source_count: dict[int, int] = {}

            owned_ids = [item[0] for item in owned_items]
            owned_weights = {item[0]: item[1] for item in owned_items}

            placeholders = ",".join("?" * len(owned_ids))
            neighbor_rows = conn.execute(
                f"""SELECT release_id, neighbor_id, score
                    FROM release_neighbors
                    WHERE release_id IN ({placeholders})""",
                owned_ids,
            ).fetchall()

            for row in neighbor_rows:
                nid = row["neighbor_id"]
                if nid in excluded_ids:
                    continue
                weight = owned_weights.get(row["release_id"], 1)
                score_map[nid] = score_map.get(nid, 0) + row["score"] * weight
                source_count[nid] = source_count.get(nid, 0) + 1

            # Sort by aggregate score
            ranked = sorted(score_map.items(), key=lambda x: x[1], reverse=True)

            # Fetch release details and apply hidden gems filter
            results = []
            for neighbor_id, agg_score in ranked:
                if len(results) >= limit:
                    break

                release = conn.execute(
                    "SELECT * FROM releases WHERE id = ?", (neighbor_id,)
                ).fetchone()
                if not release:
                    continue

                # Hidden gems filter: skip releases that appear in many user collections
                if hidden_gems:
                    with get_user_db() as uconn:
                        have_count = uconn.execute(
                            """SELECT COUNT(DISTINCT user_id) FROM user_collection
                               WHERE discogs_release_id = ? AND source = 'collection'""",
                            (release["discogs_id"],),
                        ).fetchone()[0]
                        if have_count > 5:  # Relative threshold for MVP
                            continue

                results.append({
                    **dict(release),
                    "score": round(agg_score, 4),
                    "recommended_from": source_count.get(neighbor_id, 0),
                })

            coll_matched = len([d for d in collection_discogs_ids if d in discogs_to_internal])
            want_matched = len([d for d in wantlist_discogs_ids if d in discogs_to_internal])

            return {
                "username": discogs_username,
                "collection_matched": coll_matched,
                "wantlist_matched": want_matched,
                "hidden_gems": hidden_gems,
                "recommendations": results,
            }

    except FileNotFoundError:
        raise HTTPException(
            503, "Database not available. Run build_db.py to generate it."
        )
