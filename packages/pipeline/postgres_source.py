"""Release source: the `mcp` PostgreSQL corpus on yoyaku-automation.

`populate_releases()` in build_db.py was written against one source — a Discogs
JSONL dump streamed by `style_cooccurrence.stream_releases()`. That dump has
never existed on the server, which is the structural reason `data/discoworld.db`
was never built and every DB-backed route fell back to the 5,000-release
preview.

This module is a second source for the same step, not a second pipeline: it
yields dicts in the JSONL dump's shape, so `populate_releases()` keeps one
insert path and one schema (rules/63 G5).

Which table, and why not the obvious one
----------------------------------------
`mcp` holds 15,080,106 rows in `releases`, and that number is the one everyone
quotes. It is the wrong table for DiscoWorld. Measured 2026-08-11:

    releases : year IS NULL on every row sampled (0/77,431), data = '{}'
    masters  : 1,012,900 rows — 94% carry a year, 98% carry YouTube videos,
               100% carry artists, 88% carry styles

`releases` is an identity corpus: it exists so `/mcp/resolve/catno` can turn a
catalogue number into a release id, and it carries exactly the columns that
serves. DiscoWorld is a timeline — without a year it has nothing to draw. So the
corpus is `masters`, and 1M rich rows beat 15M empty ones for this consumer.

`main_release_id` (100% populated) is used as `discogs_id` rather than the
master id, because it is a real Discogs *release* id — which is what the artwork
cache keys on (`packages/api/artwork.py`) and what `by-discogs` expects on the
YOYAKU side. Keying on the master id would silently break both.

Why the title comes from `releases`, not from `masters`
-------------------------------------------------------
`masters.title` is not a Discogs master title in this corpus — it holds the
title of the YouTube video the row was enriched from. Sampled 2026-08-11:
"Skitsystem   Stigmata FULL ALBUM", "FBD Project  The Core no label promo",
"Rockets - Ideomatic (Discoring 1982)". Only 1,011 of 2,547 sampled rows matched
the clean release title, and 905 carried the artist name inside the title, which
would render as the artist twice in the UI.

`releases.title` is clean ("Stockholm", "Starved", "Hope And Pray"), so it wins
where it exists. The rest of `masters` was checked rather than assumed: `year`
spans 1950-2025 with a release-shaped curve (rising through the 1990s, peaking
1995-2014), not the post-2005 cliff a video-upload year would produce. So the
year is the record's, and only the title was polluted.
"""

import os
from typing import Iterator

# No credential lives in this file, and none needs to (rules/65, rules/72).
# The build runs on the host that owns the database, over the local Unix socket
# under peer authentication — so the identity is the OS user, and there is no
# password to store, rotate or leak. Override with DISCOWORLD_PG_DSN when
# building from elsewhere; that DSN then carries its own credentials from the
# environment, never from source.
#
# Read-only is enforced on the session (`set_session(readonly=True)` below), not
# merely by convention: the connection cannot write whatever role it runs as.
PG_DSN_ENV = "DISCOWORLD_PG_DSN"
DEFAULT_DSN = "dbname=mcp"

# One row per master, with label/catno/country reached through the master's
# main release. LATERAL + LIMIT 1 picks a single label per release: the schema
# allows several (rel_labels is keyed on release_id + label_id) and the target
# `releases` table has one `label` column, so the choice is forced. First by
# label_id keeps it deterministic across rebuilds.
STREAM_SQL = """
SELECT
    m.main_release_id                    AS release_id,
    COALESCE(r.title, m.title)           AS title,
    m.year                               AS year,
    COALESCE(NULLIF(r.styles, '{}'), m.styles) AS styles,
    m.artists                            AS artists,
    m.videos                             AS videos,
    r.country                            AS country,
    lab.name                             AS label_name,
    rl.catno                             AS catno
FROM masters m
LEFT JOIN releases r ON r.id = m.main_release_id
LEFT JOIN LATERAL (
    SELECT label_id, catno
    FROM rel_labels
    WHERE release_id = m.main_release_id
    ORDER BY label_id
    LIMIT 1
) rl ON TRUE
LEFT JOIN labels lab ON lab.id = rl.label_id
WHERE m.year IS NOT NULL
  AND m.year > 0
  AND m.main_release_id IS NOT NULL
"""


def _youtube_videos(videos) -> list:
    """Normalize `masters.videos` to the JSONL dump's `[{"uri": ...}]` shape.

    Postgres stores the link under `src`; the Discogs JSONL dump calls it `uri`,
    and that is the key `populate_releases()` reads. Translating here keeps the
    consumer identical for both sources.
    """
    if not videos:
        return []
    out = []
    for v in videos:
        if not isinstance(v, dict):
            continue
        uri = v.get("src") or v.get("uri")
        if uri:
            out.append({"uri": uri})
    return out


def stream_releases_from_postgres(
    dsn: str | None = None,
    limit: int | None = None,
) -> Iterator[dict]:
    """Yield releases from `mcp.masters` in the JSONL dump's shape.

    Uses a named (server-side) cursor: 1M rows must not be materialized client
    side, and the build host also serves label.yoyaku.fr and inventory — a
    1M-row fetchall there is how the 2026-08-09 OOM happened.

    Keys the consumer reads are all present; `formats` is deliberately absent
    rather than empty, because `r.get("formats", [{}])[0]` raises IndexError on
    an empty list and returns a harmless `{}` when the key is missing.
    """
    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(dsn or os.environ.get(PG_DSN_ENV) or DEFAULT_DSN)
    try:
        conn.set_session(readonly=True, autocommit=False)
        # Named cursor => server-side; itersize caps each network round trip.
        cur = conn.cursor("discoworld_stream", cursor_factory=psycopg2.extras.DictCursor)
        cur.itersize = 5000
        sql = STREAM_SQL + (f" LIMIT {int(limit)}" if limit else "")
        cur.execute(sql)

        for row in cur:
            artists = row["artists"] or []
            first_artist = artists[0].get("name") if artists and isinstance(artists[0], dict) else None

            record = {
                "id": row["release_id"],
                "title": row["title"] or "",
                "artists": [{"name": first_artist}] if first_artist else [{}],
                "country": row["country"],
                "year": row["year"],
                "styles": list(row["styles"] or []),
                "videos": _youtube_videos(row["videos"]),
            }
            if row["label_name"]:
                record["labels"] = [{"name": row["label_name"], "catno": row["catno"] or ""}]
            yield record

        cur.close()
    finally:
        conn.close()
