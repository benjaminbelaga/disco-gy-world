"""Crate neighbors API — collaborative filtering recommendations.

Serves "crate neighbors" (releases commonly found in same vinyl collections)
and merged collaborative + content-based recommendations.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from ..db import get_db

router = APIRouter(tags=["crate-neighbors"])

# ---------------------------------------------------------------------------
# CF database connection
# ---------------------------------------------------------------------------

_CF_DB_PATHS = [
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "discoworld_cf.db",
    Path("/var/www/world.yoyaku.io/data/discoworld_cf.db"),
]


def _get_cf_db_path() -> Path | None:
    for p in _CF_DB_PATHS:
        if p.exists():
            return p
    return None


@contextmanager
def get_cf_db():
    """Context manager for the collaborative filtering database."""
    path = _get_cf_db_path()
    if path is None:
        raise FileNotFoundError("CF database not found. Run collaborative_filter.py first.")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/api/crate-neighbors/{release_id}")
def get_crate_neighbors(
    release_id: int,
    limit: int = Query(20, le=50),
):
    """Get releases commonly found in the same vinyl collections.

    Uses pre-computed collaborative filtering (ALS matrix factorization)
    on crawled public Discogs collections.

    The release_id can be either an internal ID or a Discogs release ID.
    """
    try:
        # Resolve to internal ID if needed
        with get_db() as main_conn:
            release = main_conn.execute(
                "SELECT id, discogs_id, title, artist, label FROM releases WHERE id = ? OR discogs_id = ?",
                (release_id, release_id),
            ).fetchone()

        # Use discogs_id for CF lookup (crawler stores discogs IDs)
        lookup_id = release["discogs_id"] if release else release_id

    except FileNotFoundError:
        lookup_id = release_id
        release = None

    try:
        with get_cf_db() as cf_conn:
            rows = cf_conn.execute(
                """SELECT neighbor_id, score FROM cf_neighbors
                   WHERE release_id = ?
                   ORDER BY score DESC LIMIT ?""",
                (lookup_id, limit),
            ).fetchall()

            if not rows:
                return {
                    "release_id": release_id,
                    "release": dict(release) if release else None,
                    "crate_neighbors": [],
                    "message": "No crate neighbors found. This release may not be in enough collections.",
                }

            # Enrich with release metadata from main DB
            neighbor_ids = [r["neighbor_id"] for r in rows]
            scores = {r["neighbor_id"]: r["score"] for r in rows}

            enriched = []
            try:
                with get_db() as main_conn:
                    placeholders = ",".join("?" * len(neighbor_ids))
                    meta_rows = main_conn.execute(
                        f"""SELECT id, discogs_id, title, artist, label, year, styles, country
                            FROM releases WHERE discogs_id IN ({placeholders})""",
                        neighbor_ids,
                    ).fetchall()
                    meta_map = {r["discogs_id"]: dict(r) for r in meta_rows}
            except FileNotFoundError:
                meta_map = {}

            for nid in neighbor_ids:
                entry = meta_map.get(nid, {"discogs_id": nid})
                entry["cf_score"] = scores[nid]
                enriched.append(entry)

            return {
                "release_id": release_id,
                "release": dict(release) if release else None,
                "crate_neighbors": enriched,
            }

    except FileNotFoundError:
        raise HTTPException(
            503,
            "Collaborative filtering data not available. "
            "Run collection_crawler.py + collaborative_filter.py first.",
        )


@router.get("/api/recommendations/collaborative")
def collaborative_recommendations(
    discogs_username: str = Query(..., description="Discogs username (public collection)"),
    limit: int = Query(30, le=100),
    content_weight: float = Query(0.6, ge=0, le=1, description="Weight for content-based score"),
    cf_weight: float = Query(0.4, ge=0, le=1, description="Weight for collaborative filtering score"),
):
    """Merged recommendations: content-based + collaborative filtering.

    For each release the user owns:
    1. Get content-based neighbors (from release_neighbors table)
    2. Get collaborative neighbors (from cf_neighbors table)
    3. Merge scores: content_weight * content_score + cf_weight * cf_score
    4. Exclude releases the user already owns or has on wantlist
    5. Return ranked, deduplicated results
    """
    from ..discogs_client import fetch_all_collection, fetch_all_wantlist

    # Fetch user's collection
    try:
        collection = fetch_all_collection(discogs_username, token=None)
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(404, f"Discogs user '{discogs_username}' not found")
        if "403" in str(e):
            raise HTTPException(403, f"Collection for '{discogs_username}' is private")
        raise HTTPException(502, f"Discogs API error: {e}")

    try:
        wantlist = fetch_all_wantlist(discogs_username, token=None)
    except Exception:
        wantlist = []

    # Extract owned release IDs
    owned_discogs_ids = set()
    for rel in collection:
        basic = rel.get("basic_information", {})
        rid = basic.get("id") or rel.get("id")
        if rid:
            owned_discogs_ids.add(rid)

    excluded_ids = set(owned_discogs_ids)
    for want in wantlist:
        basic = want.get("basic_information", {})
        rid = basic.get("id") or want.get("id")
        if rid:
            excluded_ids.add(rid)

    if not owned_discogs_ids:
        return {
            "username": discogs_username,
            "collection_size": 0,
            "recommendations": [],
            "message": "No releases found in collection.",
        }

    # Score aggregation: {release_id -> {"content": score, "cf": score, "sources": count}}
    score_map: dict[int, dict] = {}

    def add_score(rid: int, score: float, source: str):
        if rid in excluded_ids:
            return
        if rid not in score_map:
            score_map[rid] = {"content": 0.0, "cf": 0.0, "sources": 0}
        score_map[rid][source] = max(score_map[rid][source], score)
        score_map[rid]["sources"] += 1

    # Content-based neighbors
    try:
        with get_db() as main_conn:
            # Map owned discogs IDs to internal IDs
            placeholders = ",".join("?" * len(owned_discogs_ids))
            owned_internal = main_conn.execute(
                f"SELECT id, discogs_id FROM releases WHERE discogs_id IN ({placeholders})",
                list(owned_discogs_ids),
            ).fetchall()

            internal_to_discogs = {r["id"]: r["discogs_id"] for r in owned_internal}
            discogs_to_internal = {r["discogs_id"]: r["id"] for r in owned_internal}

            if owned_internal:
                internal_ids = [r["id"] for r in owned_internal]
                placeholders = ",".join("?" * len(internal_ids))
                content_rows = main_conn.execute(
                    f"""SELECT rn.release_id, rn.neighbor_id, rn.score, r.discogs_id
                        FROM release_neighbors rn
                        JOIN releases r ON r.id = rn.neighbor_id
                        WHERE rn.release_id IN ({placeholders})""",
                    internal_ids,
                ).fetchall()

                for row in content_rows:
                    add_score(row["discogs_id"], row["score"], "content")
    except FileNotFoundError:
        pass  # No main DB, skip content-based

    # Collaborative filtering neighbors
    try:
        with get_cf_db() as cf_conn:
            placeholders = ",".join("?" * len(owned_discogs_ids))
            cf_rows = cf_conn.execute(
                f"""SELECT release_id, neighbor_id, score FROM cf_neighbors
                    WHERE release_id IN ({placeholders})""",
                list(owned_discogs_ids),
            ).fetchall()

            for row in cf_rows:
                add_score(row["neighbor_id"], row["score"], "cf")
    except FileNotFoundError:
        pass  # No CF DB, skip collaborative

    if not score_map:
        return {
            "username": discogs_username,
            "collection_size": len(owned_discogs_ids),
            "recommendations": [],
            "message": "No recommendations found. Collection may not overlap with indexed releases.",
        }

    # Merge scores
    merged = []
    for rid, scores in score_map.items():
        combined = content_weight * scores["content"] + cf_weight * scores["cf"]
        merged.append({
            "discogs_id": rid,
            "combined_score": round(combined, 4),
            "content_score": round(scores["content"], 4),
            "cf_score": round(scores["cf"], 4),
            "recommended_from": scores["sources"],
        })

    # Sort by combined score, take top N
    merged.sort(key=lambda x: x["combined_score"], reverse=True)
    merged = merged[:limit]

    # Enrich with metadata
    try:
        with get_db() as main_conn:
            result_ids = [m["discogs_id"] for m in merged]
            placeholders = ",".join("?" * len(result_ids))
            meta_rows = main_conn.execute(
                f"""SELECT discogs_id, title, artist, label, year, styles, country
                    FROM releases WHERE discogs_id IN ({placeholders})""",
                result_ids,
            ).fetchall()
            meta_map = {r["discogs_id"]: dict(r) for r in meta_rows}

            for entry in merged:
                meta = meta_map.get(entry["discogs_id"], {})
                entry.update(meta)
    except FileNotFoundError:
        pass

    return {
        "username": discogs_username,
        "collection_size": len(owned_discogs_ids),
        "collection_matched": len(
            [d for d in owned_discogs_ids if d in (discogs_to_internal if 'discogs_to_internal' in dir() else {})]
        ),
        "content_weight": content_weight,
        "cf_weight": cf_weight,
        "recommendations": merged,
    }
