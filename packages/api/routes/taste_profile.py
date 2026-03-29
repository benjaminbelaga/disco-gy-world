"""Taste profile analysis — collection analytics and gap detection.

Analyzes a Discogs user's collection to produce genre distribution, style vectors,
diversity/rarity scores, timeline, top labels, and gap analysis.

Works WITHOUT OAuth: accepts ?discogs_username=xxx.
Requires collection to be synced first (call /api/recommendations/personal to trigger).
"""

import json
import math
from collections import Counter, defaultdict

from fastapi import APIRouter, HTTPException, Query

from ..db import get_db
from ..user_db import get_user_db

router = APIRouter(prefix="/api/taste-profile", tags=["taste-profile"])


def _parse_styles(styles_json: str | None) -> list[str]:
    """Parse the JSON array stored in releases.styles."""
    if not styles_json:
        return []
    try:
        parsed = json.loads(styles_json)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return [s.strip() for s in str(styles_json).split(",") if s.strip()]


def _decade_bucket(year: int | None) -> str | None:
    if not year or year < 1950:
        return None
    return f"{(year // 10) * 10}s"


def _shannon_diversity(counts: dict[str, int | float]) -> float:
    """Shannon entropy normalized to 0-10 scale.

    0 = single genre, 10 = maximally diverse.
    """
    total = sum(counts.values())
    if total == 0:
        return 0.0

    n = len(counts)
    if n <= 1:
        return 0.0

    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    max_entropy = math.log2(n)
    return round((entropy / max_entropy) * 10, 1) if max_entropy > 0 else 0.0


@router.get("")
def taste_profile(
    discogs_username: str = Query(..., description="Discogs username"),
):
    """Analyze a user's collection and return a full taste profile.

    Call /api/recommendations/personal?discogs_username=xxx first to sync
    the collection if not already done.

    Returns:
    - genre_distribution: genre -> count (via taxonomy_bridge mapping)
    - style_vector: top 50 Discogs styles weighted by rating
    - diversity_score: 0-10 Shannon entropy across genres
    - rarity_score: % of collection from labels with < 100 releases in DB
    - timeline: decade -> count
    - top_labels: [{name, count}]
    - gap_analysis: adjacent genres with 0 coverage
    """
    # Get user's collection from user_db
    with get_user_db() as uconn:
        user = uconn.execute(
            "SELECT id, synced_at FROM users WHERE discogs_username = ?",
            (discogs_username,),
        ).fetchone()

        if not user or not user["synced_at"]:
            raise HTTPException(
                400,
                f"Collection not synced yet for '{discogs_username}'. "
                f"Call /api/recommendations/personal?discogs_username={discogs_username} first.",
            )

        coll_rows = uconn.execute(
            """SELECT discogs_release_id, rating
               FROM user_collection
               WHERE user_id = ? AND source = 'collection'""",
            (user["id"],),
        ).fetchall()

    if not coll_rows:
        raise HTTPException(
            404,
            f"No collection data for '{discogs_username}'. "
            "Sync first via /api/recommendations/personal.",
        )

    # Map discogs_release_ids to main DB releases
    discogs_ids = [r["discogs_release_id"] for r in coll_rows]
    rating_map = {r["discogs_release_id"]: r["rating"] or 1 for r in coll_rows}

    try:
        with get_db() as conn:
            placeholders = ",".join("?" * len(discogs_ids))
            releases = conn.execute(
                f"SELECT * FROM releases WHERE discogs_id IN ({placeholders})",
                discogs_ids,
            ).fetchall()

            if not releases:
                return {
                    "username": discogs_username,
                    "collection_size": len(coll_rows),
                    "matched_in_db": 0,
                    "genre_distribution": {},
                    "style_vector": {},
                    "diversity_score": 0,
                    "rarity_score": 0,
                    "timeline": {},
                    "top_labels": [],
                    "top_countries": {},
                    "gap_analysis": [],
                    "message": "No releases matched our database (vinyl electronic only).",
                }

            # Load taxonomy bridge: Discogs style -> genre(s)
            bridge_rows = conn.execute(
                """SELECT tb.discogs_style, g.name as genre_name, tb.confidence
                   FROM taxonomy_bridge tb
                   JOIN genres g ON g.id = tb.genre_id"""
            ).fetchall()
            style_to_genres: dict[str, list[tuple[str, float]]] = defaultdict(list)
            for row in bridge_rows:
                style_to_genres[row["discogs_style"]].append(
                    (row["genre_name"], row["confidence"])
                )

            # Load genre links for gap analysis
            link_rows = conn.execute(
                """SELECT gs.name as source_name, gt.name as target_name, gl.weight
                   FROM genre_links gl
                   JOIN genres gs ON gs.id = gl.source_id
                   JOIN genres gt ON gt.id = gl.target_id"""
            ).fetchall()
            genre_neighbors: dict[str, list[tuple[str, float]]] = defaultdict(list)
            for row in link_rows:
                genre_neighbors[row["source_name"]].append(
                    (row["target_name"], row["weight"])
                )
                genre_neighbors[row["target_name"]].append(
                    (row["source_name"], row["weight"])
                )

            # Aggregate stats
            genre_counts: Counter = Counter()
            style_counts: Counter = Counter()
            decade_counts: Counter = Counter()
            label_counts: Counter = Counter()
            country_counts: Counter = Counter()
            label_names_seen: set = set()

            for release in releases:
                discogs_id = release["discogs_id"]
                rating = rating_map.get(discogs_id, 1)
                styles = _parse_styles(release["styles"])
                year = release["year"]
                label = release["label"]

                # Style vector (weighted by user rating)
                for style in styles:
                    style_counts[style] += rating

                    # Map to genre via taxonomy bridge
                    if style in style_to_genres:
                        for genre_name, confidence in style_to_genres[style]:
                            genre_counts[genre_name] += rating * confidence
                    else:
                        # Fallback: use style as-is
                        genre_counts[style] += rating

                # Timeline
                decade = _decade_bucket(year)
                if decade:
                    decade_counts[decade] += 1

                # Labels
                if label:
                    label_counts[label] += 1
                    label_names_seen.add(label)

                # Countries
                if release["country"]:
                    country_counts[release["country"]] += 1

            # Rarity score: % of collection from labels with < 100 releases in our DB
            label_release_counts = {}
            for label_name in label_names_seen:
                row = conn.execute(
                    "SELECT COUNT(*) FROM releases WHERE label = ?",
                    (label_name,),
                ).fetchone()
                label_release_counts[label_name] = row[0] if row else 0

            rare_count = sum(
                1
                for release in releases
                if release["label"]
                and label_release_counts.get(release["label"], 0) < 100
            )
            total_matched = len(releases)
            rarity_score = (
                round(rare_count / total_matched * 100, 1)
                if total_matched > 0
                else 0
            )

            # Diversity score
            rounded_genres = {
                k: round(v) for k, v in genre_counts.items() if v > 0
            }
            diversity = _shannon_diversity(rounded_genres)

            # Gap analysis: find adjacent genres with 0 coverage
            user_genres = set(rounded_genres.keys())
            gap_messages = []
            sorted_genres = sorted(
                rounded_genres.items(), key=lambda x: x[1], reverse=True
            )

            seen_gaps = set()
            for genre_name, count in sorted_genres[:15]:
                if count < 3:
                    continue
                neighbors = genre_neighbors.get(genre_name, [])
                for neighbor_name, _w in neighbors:
                    if neighbor_name not in user_genres and neighbor_name not in seen_gaps:
                        gap_messages.append(
                            f"You have {count} {genre_name} but 0 {neighbor_name}"
                        )
                        seen_gaps.add(neighbor_name)
                        if len(gap_messages) >= 10:
                            break
                if len(gap_messages) >= 10:
                    break

            # Format genres as array with percentages (frontend-compatible)
            sorted_genre_list = sorted(
                rounded_genres.items(), key=lambda x: x[1], reverse=True
            )
            total_genre_weight = sum(v for _, v in sorted_genre_list) or 1
            genres_array = [
                {
                    "name": name,
                    "count": count,
                    "pct": round(count / total_genre_weight * 100, 1),
                }
                for name, count in sorted_genre_list
            ]

            # Format styles as array with percentages
            sorted_style_list = style_counts.most_common(15)
            total_style_weight = sum(v for _, v in sorted_style_list) or 1
            styles_array = [
                {
                    "name": name,
                    "count": count,
                    "pct": round(count / total_style_weight * 100, 1),
                }
                for name, count in sorted_style_list
            ]

            # Format decades as array
            sorted_decades = sorted(decade_counts.items())
            total_decade = sum(v for _, v in sorted_decades) or 1
            decades_array = [
                {
                    "decade": decade,
                    "count": count,
                    "pct": round(count / total_decade * 100, 1),
                }
                for decade, count in sorted_decades
            ]

            # Format gaps as objects with genre + reason
            gaps_formatted = []
            for msg in gap_messages:
                # Parse "You have N genre but 0 other_genre"
                parts = msg.split(" but 0 ")
                if len(parts) == 2:
                    gaps_formatted.append({
                        "genre": parts[1],
                        "reason": msg,
                    })
                else:
                    gaps_formatted.append({"genre": msg, "reason": msg})

            return {
                "username": discogs_username,
                "total_releases": len(coll_rows),
                "matched_in_db": total_matched,
                "genres": genres_array,
                "styles": styles_array,
                "diversity_score": diversity,
                "rarity_score": rarity_score,
                "decades": decades_array,
                "top_labels": [
                    {"name": name, "count": count}
                    for name, count in label_counts.most_common(20)
                ],
                "top_countries": dict(country_counts.most_common(10)),
                "gaps": gaps_formatted,
                "wantlist_count": 0,
            }

    except FileNotFoundError:
        raise HTTPException(
            503, "Database not available. Run build_db.py to generate it."
        )
