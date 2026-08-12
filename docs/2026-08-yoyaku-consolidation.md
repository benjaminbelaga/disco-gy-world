# YOYAKU consolidation — 2026-08

## Purpose

DiscoWorld, `disco.gy`, YOYAKU's shop, and the iOS app are independent
products. They do not share a runtime, deployment process, or licence boundary.
The integration contract is therefore data and HTTP, never a shared client
package or a monorepo merge.

This document is the maintained product/technical handoff for the 2026-08
consolidation. The forensic record, measurements, commands, and operational
rollbacks remain in the intervention log linked below.

## Delivered

### Discovery corpus

- DiscoWorld now builds `data/discoworld.db` from the local `mcp` PostgreSQL
  corpus's `masters` table, then unions in the curated 5,000-release preview.
  The preview is deliberately retained: only 218 of its releases appeared in
  the masters source, so replacing it would erase curation.
- The built corpus contains 969,064 releases rather than falling back to the
  5,000-row browser preview. Artist timelines, search, labels, and dynamic API
  routes use it.
- `artists` routes use exact artist matching first, are bounded to 500 timeline
  records, and read the taxonomy bridge once per request. This preserves
  interactive response times at corpus scale.

### YOYAKU commerce context

- The shop catalogue is a fourth build source. A carried record has `sku` and
  `shop_url`; price and inventory are intentionally not copied into the corpus
  because they change faster than a corpus build.
- A Discogs release ID identifies a pressing, not necessarily the record that a
  customer sees in the shop. The useful bridge is a guarded, normalized
  catalogue-number match: at least four characters, including a letter and a
  digit. It increases the measured overlap from 618 exact pressing matches to
  7,545 catalogue-number matches while excluding sentinel and bare-number
  collisions.
- A catalogue-number match is a discovery hint, not proof of a specific
  pressing. The shop URL is the authority for the purchasable item.

### Product and reliability fixes

- Dynamic routes no longer answer `503 Database not available` merely because a
  full SQLite corpus file is absent: the 5,000-row preview remains an honest
  fallback.
- Genre-panel cover art is resolved server-side through a cached Discogs API
  adapter. Positive entries live for 90 days and missing artwork for seven;
  browser clients never spend the Discogs rate limit directly.
- `THREE.Clock` was replaced by `THREE.Timer`, stale YouTube players are torn
  down before their iframe is removed, and the broken cross-origin YOYAKU
  password form was removed. The only supported sign-in remains Discogs OAuth.

## Current product boundary

The right-hand GenrePanel intentionally still reads `releases_preview.json`.
It is an editorial selection, not a corpus browser. The 969k corpus powers
search, timelines, artist, and label surfaces instead.

Do not replace that panel's curated selection autonomously. The product choice
is whether it should remain a focused, curated route into the world or become a
searchable corpus view. On the current selection, only roughly 101/5,000 rows
would show a YOYAKU commerce hint, even after catalogue-number matching.

## Roadmap

### Next autonomous work

1. Make corpus builds reproducible on the server: replace the unversioned
   `/opt/discoworld-pipeline/` copy with a checkout or a documented rsync from
   this repository.
2. Decide the refresh cadence with the owner of the `mcp` corpus, then automate
   the shop export and corpus rebuild as one observable job.
3. Re-measure and repair the documented `/mcp/search/release` and
   `/mcp/search/artist` routes that have hung in production. Keep this separate
   from the DiscoWorld API deployment.
4. Add FTS5 only if real usage shows the bounded substring search (~1.1s on the
   current corpus) harms discovery.

### Owner decision required

1. Decide whether the GenrePanel remains curated or becomes a corpus surface.
2. Decide the identity model before connecting purchase history to
   Discogs-based recommendations. Never reintroduce a cross-origin shop-password
   form; a proper account-link/OAuth flow is required.
3. Consolidate the three WordPress CORS allowlists in an isolated deployment
   only when a browser-side integration actually requires it. Server-side
   commerce and audio lookups do not require CORS.

## Boundaries that must remain

- Preserve the 166-node Ishkur presentation taxonomy. Use a bridge for joins;
  do not flatten it into shop genres.
- Keep the player implementations separate by platform. Share audio contracts,
  not player code.
- Keep private YOYAKU commerce logic out of this AGPL repository. The public
  surface may consume the derived `shop_url`/`sku` fields only.
- Keep the preview fallback. A missing corpus must degrade to a smaller but
  working product, not to a 503.

## Evidence and related records

- Implementation commits: `1794e6b`, `576738f`, `cab2577`, `b8ec01d`.
- Earlier artwork and console fixes: `7d5c2b2`, `0f35430`.
- Operational evidence and open technical items:
  `logs-infra/interventions/2026-08-11-discoworld-corpus-from-mcp-masters.md`.
- Cross-surface working plan (local operational artifact):
  `~/.claude/plans/reprends-i-i-exported-14-synthetic-turtle.md`.
