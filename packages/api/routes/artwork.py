"""Artwork endpoint — cover art for releases, by Discogs release id."""

from fastapi import APIRouter, HTTPException, Query

from ..artwork import resolve

router = APIRouter(prefix="/api/artwork", tags=["artwork"])

# One panel shows ten rows. The cap is above that so a single view is always one
# request, and low enough that a crafted URL cannot fan out into a rate-limit
# burn on a cold cache.
MAX_IDS = 25


@router.get("")
def artwork_batch(
    ids: str = Query(..., description="Comma-separated Discogs release ids"),
    cached_only: bool = Query(False, description="Skip the Discogs call; return only what is cached"),
):
    """Resolve artwork for up to 25 release ids in one call.

    Batched deliberately: the browser asks once per panel rather than once per
    row, which keeps the server in control of how much of the 60 req/min Discogs
    budget a render can spend.
    """
    parsed: list[int] = []
    for raw in ids.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            parsed.append(int(raw))
        except ValueError:
            # Skip junk rather than 400 — one bad id in a list should not cost
            # the caller the other twenty-four covers.
            continue

    if not parsed:
        raise HTTPException(400, "No valid release ids.")
    if len(parsed) > MAX_IDS:
        raise HTTPException(400, f"Too many ids (max {MAX_IDS}).")

    # Preserve caller order, drop duplicates.
    seen: set[int] = set()
    ordered = [i for i in parsed if not (i in seen or seen.add(i))]

    resolved = resolve(ordered, allow_fetch=not cached_only)
    return {
        "artwork": {str(rid): resolved[rid] for rid in ordered if rid in resolved},
        "requested": len(ordered),
        "resolved": len(resolved),
    }
