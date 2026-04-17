# AGENT F — Competitor Feature Matrix

**Mission:** brutal honest comparison of music-discovery / spatial-music apps vs **DiscoWorld (world.yoyaku.io)**.
**Date:** 2026-04-17
**Method:** direct fetch of live homepages + meta + JSON-LD + JS bundle sniffing + cross-refs with `memory/discoworld-roadmap.md`.

---

## 1. DiscoWorld — reference feature set (what WE have)

- 3D **globe** with 49 cities (Three.js)
- 3D **genre galaxy** (166 genres) + genre-planet view
- Navigation: **earth ↔ genre ↔ planet**
- **YouTube** player with queue
- **Drift mode** (auto-exploration)
- **Dig Path** (URL-shareable exploration trail)
- **Mystery node** (serendipity)
- **Discogs + YOYAKU OAuth**
- **PWA**, deep-links (`view/city/genre/lat/lng/year/drift`)
- Share button, Onboarding modal, Favorites, Collection / Passport

Implicit positioning: music-exploration-as-spatial-ritual, tied to a real-world shop (YOYAKU) + Objects pressing pipeline.

---

## 2. Competitor profiles

### 2.1 zig-zag.fm — **the closest analog**
- **URL:** https://zig-zag.fm
- **Team / status:** Hugo + Anto + Moritz. Active (launched 2025, r/TheOverload viral ~2025-12). JSON-LD declares `foundingDate: 2025`, free (offers price 0 USD).
- **Tech:** React + React-Query + i18n + **AWS SDK** (storage/cognito-like) + **deck.gl** (2D map engine) + vendor-analytics bundle. Preconnects: `i.ytimg.com`, `www.youtube.com` → **YouTube is their playback layer too**.
- **Core interaction:** 2D zoomable map tiled via deck.gl. "Interactive map for music digging — genres, cities, subgenres, periods, labels, tracks connected on a living map." 1.5M releases, 7M tracks, 800k artists claimed.
- **Stand-out:** continents-with-cultural-coherence feel (manual post-UMAP layout), cream palette (readable), search endpoint `/?q=`, massive catalog scale.
- **Weakness:** 2D only, no audio preview beyond YouTube, no OAuth, no collection import, no PWA manifest for installability despite `manifest.webmanifest` (basic), no native sharing of dig-path, no city-as-first-class-citizen (cities are mixed in the flat map).

### 2.2 everynoise.com — **the classic 2D tile**
- **URL:** https://everynoise.com
- **Team / status:** Glenn McDonald (ex-Spotify). "Active" but zombie since Spotify let him go (Dec 2023). Many links marked `.broken`. No updates to underlying Spotify preview API since their shutdown.
- **Tech:** vanilla HTML + inline CSS, one giant page, `spotproxy.cgi` for preview URLs, ~6000 genre tiles absolutely positioned.
- **Core interaction:** click a genre → 30s Spotify preview plays. Spatial 2D layout: y-axis = organic→mechanical, x-axis = dense→spiky.
- **Stand-out:** 6000+ genres, axis-meaningful layout, the cultural reference everyone copies.
- **Weakness:** fragile (Spotify API rot = "broken" tags everywhere), no mobile story, no OAuth, no collection, no share state, no 3D, zero dev velocity.

### 2.3 music-map.com (gnod)
- **URL:** https://www.music-map.com
- **Team / status:** gnod global network of discovery. Active but 2005-era UX.
- **Tech:** PHP + jQuery + typeahead. Static layout, no modern JS framework.
- **Core interaction:** type an artist → 2D force-directed "gnoosic cloud" of similar artists. Click any name to re-center.
- **Stand-out:** pure artist-similarity, instant, no account. Recognizable brand.
- **Weakness:** no audio, no genres, no cities, no eras. No API. Feels like 2008.

### 2.4 radiooooo.com
- **URL:** https://radiooooo.com
- **Team / status:** Active. French project since 2014, Mapbox-backed. iOS + Android apps (`al:ios:app_store_id 893151807`).
- **Tech:** custom JS bundle, Mapbox GL, Cloudflare fonts, ServiceWorker + manifest (PWA-ish). CDN `static.radiooooo.com`, `asset.radiooooo.com`.
- **Core interaction:** pick a **country + decade** (1900s → 2020s) → curated radio stream plays. "Musical Time Machine."
- **Stand-out:** **era × country = 2D matrix**, human-curated library (users submit, editors approve), mobile apps, strong brand, **paid tier** ("Classic/Premium" unlocks all decades & countries).
- **Weakness:** no genre dimension, no similarity, no collection-import, no share-state beyond permalink, no user account for external services.

### 2.5 cosine.club
- **URL:** https://cosine.club
- **Team / status:** Active, small team. Sentry + Plausible analytics, HTMX + Tailwind + surreal.js — indie-ML stack.
- **Tech:** HTMX server-rendered, custom vendor bundle, Plausible self-hosted (`analytics.cosine.club`). No 3D, no map.
- **Core interaction:** paste a track → ML similarity search returns similar tracks + "explore playlists."
- **Stand-out:** **audio-embedding similarity** (not just metadata / tag co-occurrence). Clean UX, keyboard-first.
- **Weakness:** no spatial layout, no genre tree, no cities, no eras, no OAuth, no collection, solo-track focus.

### 2.6 rateyourmusic.com/genres
- **URL:** https://rateyourmusic.com/genres/
- **Team / status:** Active (Sonemic parent), Cloudflare-gated (JS challenge).
- **Tech:** server-rendered, editorially curated genre tree (RYM is THE authority for editorial taxonomy).
- **Core interaction:** browse the **genre tree** — ~1500 genres with parent/child hierarchy + top-rated releases.
- **Stand-out:** hand-curated taxonomy (no ML / no Spotify bias). Community-driven.
- **Weakness:** no audio, no map, no 3D, hostile to crawlers, no API.

### 2.7 Spotify "Browse" (genres & moods)
- **URL:** open.spotify.com/genre/...
- **Team / status:** Active, but **Glenn McDonald left** → everynoise-style taxonomy on the decline.
- **Tech:** closed. SpotifyCDN, React/Encore design system.
- **Core interaction:** editorial shelves of playlists per genre/mood.
- **Stand-out:** **playback power** (your whole library, full tracks, podcasts). Best recs engine on Earth.
- **Weakness:** walled garden, no external API for spatial rendering, no map, no era, no city, no collaborative discovery, paid.

### 2.8 maroofy.com
- **URL:** https://maroofy.com
- **Team / status:** **DEPLOYMENT_DISABLED / Payment required** (fetched 2026-04-17, Vercel error). Likely abandoned or paused.
- **Historical feature:** similarity search by track (was an ML-backed rec engine similar to cosine.club).
- **Verdict:** not an active competitor today.

### 2.9 chosic.com/genre-finder
- **URL:** https://www.chosic.com/genre-finder/
- **Team / status:** Active parent site (astra WP theme, Yoast SEO). `/genre-finder/` itself returned **404** on fetch — likely removed / renamed.
- **Historical feature:** type artist → returns Spotify genre tags + similar artists. Heavy Spotify-API wrapper.
- **Verdict:** SEO-farm-ish, Spotify-dependent, no spatial dimension.

### 2.10 New 2025-2026 entrants (reddit watch)
From `memory/discoworld-roadmap.md` + r/TheOverload:
- **zig-zag.fm** is the only serious 2025+ entrant that broke containment.
- Neal.fun has done one-off music maps (not a product).
- Various "Spotify wrapped" visualizers exist but are retrospective, not exploratory.
- No new 3D music-world product launched in the last 12 months that we've found. **DiscoWorld is alone in the 3D-globe niche.**

---

## 3. Feature matrix

Legend: **Y** = yes / strong · **~** = partial / weak · **N** = no

| Feature                | DiscoWorld | zig-zag.fm | everynoise | music-map | radiooooo | cosine.club | RYM /genres | Spotify browse | maroofy | chosic |
|------------------------|:----------:|:----------:|:----------:|:---------:|:---------:|:-----------:|:-----------:|:--------------:|:-------:|:------:|
| **3D globe**           | Y          | N          | N          | N         | N         | N           | N           | N              | N       | N      |
| **2D map**             | ~ (galaxy flattens) | Y (deck.gl) | Y (tile) | Y (force-graph) | Y (Mapbox) | N | N | N | N | N |
| **Audio preview**      | ~ (YouTube) | ~ (YouTube) | Y (Spotify 30s, fragile) | N | Y (full radio) | Y (ML) | N | Y (Spotify) | ? | ~ |
| **YouTube integration**| Y (queue)  | Y (preconnect ytimg) | N | N | N | N | N | N | N | N |
| **Genre tree**         | Y (166)    | Y (sub-genre nav) | Y (~6000) | N | N | N | Y (editorial) | Y | N | Y |
| **City view**          | Y (49)     | ~ (cities on map) | N | N | Y (country level) | N | N | N | N | N |
| **Era filter**         | ~ (year param) | Y (period) | N | N | **Y (decade-first)** | N | ~ | N | N | N |
| **Mood filter**        | N          | N | ~ (axis-implied) | N | N | N | N | Y (editorial) | N | ~ |
| **Similarity recs**    | ~ (via dig path) | Y (graph traversal) | ~ (adjacent tiles) | Y | N | Y (ML embeddings) | N | Y (closed) | Y (hist.) | Y |
| **URL deep-link**      | Y (rich)   | Y (?q=, /genre/) | ~ (#anchor) | Y | Y | ~ | Y | Y | ? | Y |
| **Share**              | Y          | ~ (copy URL) | ~ | ~ | Y | ~ | ~ | Y | ? | ~ |
| **Collection import**  | Y (Discogs + YOYAKU OAuth) | N | N | N | N | N | N | Y (own) | N | N |
| **Collaborative**      | N          | N | N | N | ~ (user submissions) | N | Y (RYM ratings) | Y (playlists) | N | N |
| **Paid tier**          | N          | N (free) | N | N | **Y** | ~ (account) | ~ (ultra) | **Y** | ? | N |
| **OAuth**              | **Y (Discogs + YOYAKU)** | N | N | N | N | ~ (email) | ~ | Y | N | N |
| **Mobile PWA**         | Y          | ~ (manifest only) | N | N | Y (native apps) | N | N | ~ | N | N |
| **Drift / auto-play**  | **Y (drift mode)** | N | ~ (scan) | N | Y (radio) | N | N | Y (radio) | N | N |
| **Dig-path / trail**   | **Y (URL-encoded)** | N | N | N | N | N | N | N | N | N |
| **Mystery / serendipity** | **Y (mystery node)** | N | ~ (scan) | N | ~ (random country) | N | N | ~ (Daily Mix) | N | N |

---

## 4. Features to steal (ranked by impact)

1. **UMAP-driven spatial layout with manual "continent" coherence** (zig-zag.fm) — fixes our "crammed cloud in the void" problem. High impact, medium effort.
2. **Cream / dawn palette + readable typography** (zig-zag.fm) — our pitch-black void is the #1 visual complaint. High impact, low effort.
3. **Era-first time machine** (radiooooo) — make year/decade a primary axis, not a URL param. Medium impact, medium effort. Differentiates from zig-zag.
4. **Human-curated editorial layer** (radiooooo + RYM) — let YOYAKU staff promote releases into the map. Medium impact, medium effort. Ties to our record-shop moat.
5. **ML audio-similarity on hover/click** (cosine.club) — "find tracks that sound like this one." High impact, high effort (need embeddings pipeline).
6. **Genre-axis meaning** (everynoise: organic→mechanical, dense→spiky) — give our 3D axes actual semantics, not just clustering noise. Medium impact, low effort.
7. **Country + decade matrix entry point** (radiooooo) — lightweight onboarding for casual users. Low effort, medium impact.
8. **Full-catalogue scale claim** (zig-zag: 1.5M releases, 7M tracks) — our Discogs + YOYAKU data can match this. Pure marketing copy. Low effort.
9. **Native mobile apps** (radiooooo) — PWA is nice but native unlocks push + lockscreen controls. High effort, high impact long-term.
10. **Paid tier / Premium unlock pattern** (radiooooo, Spotify) — revenue validation. Gate "drift mode 24/7" or "unlimited dig paths" behind €3/mo. Medium effort, direct revenue.
11. **Auto-play "radio" streaming** (radiooooo) — extend drift-mode into a lean-back continuous listening mode. Low-medium effort.
12. **Search as first-class citizen** (zig-zag `?q=`) — add a global search entry to jump anywhere in the world/galaxy. Low effort, high UX.

---

## 5. Unique moat (what nobody else has)

1. **3D globe + 3D galaxy + planet view** with smooth navigation between them. Nobody is in 3D at this UX polish level.
2. **Dig-path as URL-encoded trail** — sharable exploration history as a first-class object. Unique.
3. **Discogs + YOYAKU OAuth** — real collection-import from a real record-shop ecosystem. No competitor ties into commerce.
4. **Mystery node** — explicit serendipity primitive. No one else has named this pattern.
5. **Drift mode** — ambient auto-exploration distinct from radiooooo's passive radio (we move through space, not just play audio).
6. **Real-world shop anchoring** — YOYAKU shop + Objects pressing pipeline + preorder flows. We can surface "buy the vinyl" on any node. Zero competitors can do this.
7. **Genre planet as a zoomable 3D body** (not a flat list). Unique view.
8. **PWA + deep-link richness** (`view/city/genre/lat/lng/year/drift`) beyond anything else in the space.

---

## 6. Strategic positioning

1. **DiscoWorld is the only music explorer that lets you walk a planet of genres, orbit a globe of cities, and leave a sharable trail of your dig.**
2. **DiscoWorld is the only music explorer backed by a real record shop** — every node can end in a vinyl you actually buy.
3. **DiscoWorld is the only 3D, spatially-navigable music world** — everyone else stopped at 2D maps or tile grids. We took the leap.

---

## Appendix — raw evidence (fetched 2026-04-17)

- zig-zag.fm JSON-LD: `foundingDate 2025`, `applicationCategory MusicApplication`, `price 0 USD`, preconnects to `i.ytimg.com` + `www.youtube.com`, bundle includes `vendor-deckgl`, `vendor-aws-sdk`, `vendor-i18n`, `vendor-analytics`.
- everynoise.com: inline `spotproxy.cgi` for preview URLs; `.broken` class markup proves link rot.
- music-map.com: jQuery + typeahead, `gnod.com` parent, latest searches = commercial pop (MJ, LL Cool J, etc.).
- radiooooo.com: Mapbox + ServiceWorker + iOS App Store ID `893151807` + Android package `com.radiooooo` + Cloudflare Poppins fonts.
- cosine.club: HTMX + Tailwind + surreal.js + Plausible + Sentry; no map/3D.
- rateyourmusic.com/genres: Cloudflare JS challenge blocks crawlers, Sonemic-owned.
- Spotify browse: closed, SpotifyCDN, Encore design system, mobile-web-player bundle.
- maroofy.com: **Vercel DEPLOYMENT_DISABLED** — abandoned.
- chosic.com/genre-finder: **404**, Astra WP theme, Yoast SEO — SEO farm.
- No new 2025-2026 3D-music entrant found. DiscoWorld is alone in 3D.
