# DiscoWorld v2.0 — Mega Design Document

**Date:** 2026-03-16
**Author:** Benjamin Belaga
**Status:** Draft — awaiting review
**License:** AGPL-3.0

## 1. Vision

DiscoWorld is an open-source 3D music discovery platform that transforms Discogs' 19M-release database into an explorable world. Two modes of exploration:

- **Earth Globe** — Real geographic visualization of music scenes, labels, record shops, and distribution flows
- **Genre Planet** — A procedurally generated fictional planet where genres form continents, subgenres form territories, and releases populate the landscape

The platform serves both curious newcomers exploring electronic music for the first time and hardcore vinyl diggers seeking undiscovered releases through Discogs-powered collaborative filtering.

**Core principle:** DiscoWorld should feel like an infinite record shop where the crates organize themselves around you.

**Moat:** The intersection of 3D explorable world + Discogs data dump (4.87M electronic releases) + open source + vinyl culture is completely unoccupied. Discograph (2D graph, abandoned ~2020) is the closest ancestor.

## 2. Architecture Overview

```
                    ┌─────────────────────────────┐
                    │      DiscoWorld Frontend     │
                    │    Vite + React + globe.gl   │
                    │    + Three.js (genre world)  │
                    │    + Zustand + PostProcessing │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │      DiscoWorld API          │
                    │    FastAPI (Python)          │
                    │    SQLite + Redis cache      │
                    └──────────┬──────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐ ┌──────▼──────┐ ┌───────▼──────┐
    │  Discogs Dump  │ │ Discogs API │ │  Rec Engine  │
    │  4.87M releases│ │ OAuth 1.0a  │ │  Implicit    │
    │  JSONL/SQLite  │ │ Collections │ │  ALS model   │
    └────────────────┘ └─────────────┘ └──────────────┘
```

### Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend framework | Vite + React | Already in place, fast HMR |
| Earth Globe | globe.gl v2.45 (wraps three-globe/Three.js) | Proven by WorldMonitor, handles markers/arcs/atmosphere natively |
| Genre Planet | Raw Three.js + R3F + drei | Need custom terrain displacement, not possible with globe.gl |
| State | Zustand | Already in place, minimal, correct |
| Post-processing | three/examples/jsm (UnrealBloomPass) | Selective bloom for premium look |
| API | FastAPI (Python) | Already in place |
| Database | SQLite (data) + Redis (cache) | Lightweight, sufficient for read-heavy workload |
| Reco engine | Implicit (Python ALS) | Best for implicit feedback (owns/doesn't own), handles sparse vinyl collections |
| Discogs client | @lionralfs/discogs-client | Modern ESM fork, OAuth + collection/wantlist |
| Audio | YouTube IFrame API (iframe) | Simplest viable approach, cross-origin safe |

## 3. Dual-World System

### 3.1 Earth Globe (Geographic View)

Based on WorldMonitor's architecture, adapted for music.

**Visual identity:**
- Dark matte globe with faint continental outlines
- Atmosphere: custom Fresnel backface shader (`intensity = pow(0.7 - dot(vNormal, vec3(0,0,1)), 2.0)`) with cyan/magenta accent
- Double glow sphere (BackSide material, opacity 0.15/0.10)
- Starfield: 2K points, InstancedMesh
- UnrealBloomPass at half-res (strength=1.2, radius=0.4, threshold=0.8)
- Subtle vinyl groove normal map on globe surface
- Color palette: navy/black + cyan atmosphere + amber/gold active points

**Data layers:**
- City markers (InstancedMesh, 500 cities) — pulsing by music activity
- Label markers — clustered via Supercluster at low zoom
- Record shop markers — from OSM Overpass API (~15K worldwide)
- Distribution arcs (ArcLayer) — waveform-modulated altitude (`baseAlt + sin(t * freq) * amplitude`)
- Genre heatmap (HeatmapLayer) — release density by country
- Connection arcs between cities sharing label networks

**Data sources:**
- Phase 1: 4.87M releases × country field (58 countries)
- Phase 2: Artist city extraction from artists.xml.gz (~28% hit rate → ~1.3M with city)
- Phase 3: Label contactinfo parsing (~3% with addresses, but iconic labels)
- Phase 4: OSM record shops as navigation anchors

**Interactions:**
- OrbitControls with auto-rotate (resume after 60s idle)
- Click city → fly-to + genre panel
- Hover marker → tooltip with label name, release count, top styles
- Zoom-dependent layer visibility thresholds

### 3.2 Genre Planet (Abstract World)

A procedurally generated planet where genres form continents.

**Generation pipeline:**

```
IGTEM26 graph (251 genres, 502 weighted edges)
  + Musicmap super-genre groupings (continent clusters)
    → Force-directed layout (d3-force) with edge weights
      → Voronoi tessellation (d3-delaunay) → genre territories
        → Super-genre merge → continent landmasses
          → Perlin/Simplex noise on edges → organic coastlines
            → Heightmap: BPM=altitude, release_count=density
              → Three.js sphere + vertex displacement shader
```

Reference: Red Blob Games Polygonal Map Generation pipeline.

**Genre-to-biome mapping (terrain + architecture):**

| Super-genre | Terrain | Architecture | Sky | Signature |
|-------------|---------|-------------|-----|-----------|
| Techno | Dark volcanic rock, industrial wasteland | Brutalist towers, factory chimneys, cylinders | Dark/stormy, neon fog | Smoke particles, cyan neon strips |
| House | Rolling hills, warm savanna | Art deco, rounded arches, terracotta | Sunset, warm amber | String lights, club canopies |
| Ambient | Crystal caverns, floating islands | Glass spires, iridescent shards | Aurora, soft volumetric rays | Floating particles, slow rotation |
| Drum & Bass | Angular canyons, metallic terrain | Tilted towers, highway overpasses | Night sky, orange sparks | Suspended rail tracks, speed lines |
| Trance | Mountain plateaus, sacred geometry | Pyramids, ziggurats, domed temples | Aurora borealis, uplighting | Beam pillars, mandala floors |
| Hardcore/Gabber | Volcanic craters, jagged peaks | Bunkers, silos, radar dishes | Red sky, lightning | Explosion particles |
| Downtempo/Trip-Hop | Misty valleys, rivers | Low brick buildings, jazz clubs, cafes | Fog, dim streetlights | Rain particles |
| Experimental | Abstract geometry, impossible terrain | Non-euclidean structures | Glitch sky shader | Geometry distortion |

**Building generation:**
- Parametric: `generateBuilding(genreConfig)` → BufferGeometry
- InstancedMesh per archetype (5-8 per genre, single draw call per pool)
- Emissive window shader (fragment shader grid pattern, random on/off)
- LOD: 3 levels (detailed <100m, simplified <500m, billboard >500m)
- Low-poly stylized (`flatShading: true`)

**World transition (Earth ↔ Genre Planet):**
- Both render to WebGLRenderTarget
- Perlin noise dissolve shader for transition
- Camera path interpolation (lerp position + quaternion)
- R3F createPortal for dual-scene management

### 3.3 Taxonomy Bridge

Currently 3 disconnected taxonomy systems. Must unify:

| Source | Genres | Purpose |
|--------|--------|---------|
| IGTEM26 / Ishkur v4 | 251 + 502 edges | Graph structure, genre relationships, GeoJSON polygons |
| Custom taxonomy | 18 core + 50 sub + 16 neighbor | BPM ranges, mood tags, geography_matrix, influenced_by |
| Discogs styles | 106 unique (540 total across all genres) | Release tagging, population counts |

**Bridge strategy:**
1. IGTEM26 as the primary graph (spatial structure)
2. Map each Discogs style to its closest IGTEM26 genre(s) — many-to-many
3. Merge custom taxonomy data (BPM, mood, geography) into IGTEM26 nodes
4. Release counts from Discogs dump enrich each genre with population density
5. Style co-occurrence matrix (from dump: releases tagged with multiple styles) creates additional weighted edges

## 4. Discovery Engine

### 4.1 Three Discovery Modes

**Search** — "I know what I want"
- Enhanced vibe search: "dark 90s electro from Detroit" → natural language + structured filters
- Discogs-style filters: label, year, format, BPM range, country
- Results fly the camera to matching genre territory or city on globe

**Browse** — "I'll know it when I see it"
- Genre territories with release particles orbiting nodes
- Particle size = community importance (Discogs "have" count)
- Particle color = decade
- Click particle → mini-panel: cover art, tracklist, YouTube iframe
- Label constellations: click label name → highlight all its releases across the world
- Artist threads: visible lines connecting an artist's releases across genres

**Stumble** — "Surprise me"
- "Drift" button: camera auto-navigates, auto-plays 30-second samples from nearby releases
- Single slider: familiar ↔ adventurous (controls taste-distance wandering)
- Cross-genre bridges: releases owned by fans of 2+ different genres glow distinctively
- Time warp: random decade jump within preferred genres
- Mystery "?" node: one unlabeled genre per session near taste cluster, reveals after 3 listens

### 4.2 Recommendation Engine

**Phase 1 — Content-based (no user data, ship first):**
- Feature vector per release: style_ids (576 binary dims) + label_id + year_bucket + artist_ids
- Cosine similarity on sparse vectors, weighted by label overlap + artist graph
- Pre-compute top-50 neighbors for 385K vinyl releases → SQLite
- API: `GET /api/recommendations/{release_id}` → 10 similar releases
- Zero API calls, runs entirely from dump data

**Phase 2 — Personal (Discogs OAuth):**
- User logs in → fetch collection + wantlist (~60 API calls)
- Build taste profile: aggregate style vectors weighted by user rating
- Query Phase 1 neighbors → rank → exclude owned + wantlisted
- "Hidden gems" filter: `community_have < 500 AND similarity_score > 0.7`
- Cache indefinitely, refresh on demand

**Phase 3 — Collaborative filtering:**
- Crawl 10K public electronic collectors' collections (Contabo background job, ~83h)
- Store (user_hash, release_id) pairs only — no PII
- Implicit library (ALS matrix factorization) for binary implicit feedback
- Co-occurrence boost: releases frequently in same collections but user doesn't own
- Weekly batch re-train

### 4.3 Discogs OAuth Integration

- OAuth 1.0a flow: request_token → authorize redirect → access_token
- Library: `@lionralfs/discogs-client` (ESM + TypeScript)
- Rate limit: 60 req/min authenticated
- Collection import: 3000 records = 30 API calls = ~30 seconds
- User data stored: user_id, release_ids, ratings, wantlist, synced_at
- Public collection access enables collaborative filtering (official API feature)

## 5. Audio

YouTube IFrame API for simplicity. No Strudel, no Web Audio API (Phase 1).

- Detect play/pause via `onStateChange`
- Simulated audio reactivity (Pd-inspired): pseudo-random oscillators with lerp (already implemented in v0.7)
- Future: replace with HTML5 `<audio>` + AnalyserNode for real FFT when streamable audio sources are available

## 6. UX & Navigation

### 6.1 3D Navigation (preventing disorientation)

- **Minimap** (bottom corner): 2D top-down genre map with "you are here" dot. Click to teleport. Non-negotiable.
- **Breadcrumb trail**: luminous path fading after 60s
- **Home beacon**: bright fixed star → return to taste center
- **Progressive disclosure**: start zoomed into ONE genre cluster, full world reveals as user explores
- No dump into the void. Ever.

### 6.2 Onboarding Flow

1. Landing: "What's your vibe?" — one vibe search input, no account
2. Camera flies to matching genre cluster, 3-5 samples auto-play
3. Click release particle → panel with cover art + YouTube embed
4. After 3 likes: "Import your Discogs collection?" (optional)
5. Minimap fades in after first manual camera movement
6. Full galaxy visible after 2 minutes of exploration

### 6.3 Key UX Principles

- Zero account required for first value
- Immediate audio feedback on every interaction
- "Infinite record shop where crates organize around you"
- Transparency: always explain WHY something is recommended (shared label, similar collectors, same era)

## 7. Data Pipeline

### 7.1 What Exists (keep)

- Discogs XML dump streaming parser (`ingest_releases.py`)
- 4,870,570 electronic releases with: title, artists, labels, catno, country, year, genres, styles, formats, videos, tracklist
- 1,419,763 vinyl format releases
- 1,310,819 with YouTube links
- Ishkur dataset (v3 JSON, GeoJSON polygons)
- Custom taxonomy with geography_matrix, mood tags, BPM ranges

### 7.2 What to Build

1. **Taxonomy bridge** — IGTEM26 ↔ Discogs style mapping (many-to-many)
2. **Style co-occurrence matrix** — which styles appear together on releases (weighted edges)
3. **Release-per-genre counts** — populate genre nodes with volume data
4. **Artist city extraction** — parse artists.xml.gz, extract city from profile text (~28% hit rate)
5. **Label-to-city mapping** — parse labels.xml.gz contactinfo (~3% with addresses)
6. **Content-based similarity index** — pre-compute for 385K vinyl releases
7. **Genre world heightmap** — IGTEM26 graph → Voronoi → Perlin → displacement map
8. **OSM record shop dataset** — Overpass API query for global vinyl shops

## 8. Performance Budget

### 8.1 Earth Globe

| Component | Draw calls | Budget |
|-----------|-----------|--------|
| Globe body + atmosphere halo | 3 | Always |
| Bloom (half-res) | 3-4 passes | Always |
| Starfield (InstancedMesh) | 1 | Always |
| City markers (InstancedMesh, 500) | 1 | Always |
| Arcs (100 visible) | 1 instanced | Always |
| Record shop markers (clustered) | 1 | On zoom |
| **Total** | **~10** | **60fps mid-range laptop** |

### 8.2 Genre Planet

| Component | Draw calls | Budget |
|-----------|-----------|--------|
| Planet sphere + displacement | 1 | Always |
| Atmosphere | 1 | Always |
| Building pools (5-8 InstancedMesh per visible genre) | 5-8 | Near camera |
| Release particles | 1 instanced | Always |
| Bloom + fog | 3-4 passes | Always |
| **Total** | **~15** | **60fps desktop, 30fps mobile** |

### 8.3 Data Budget

- Initial load: <2MB (genre graph + metadata). Releases stream on demand.
- No 10.5MB upfront particle JSON. Use spatial indexing, load by viewport.
- Bootstrap hydration pattern (single batch API call on init)

## 9. Phased Delivery

### Phase 0 — Foundation (2-3 weeks)
- Taxonomy bridge (IGTEM26 + Discogs + custom → unified graph)
- Style co-occurrence matrix from dump
- Release-per-genre population counts
- Content-based similarity index (385K vinyl releases)
- API: `/recommendations/{release_id}`, `/genres`, `/releases?genre=`

### Phase 1 — Earth Globe (3-4 weeks)
- globe.gl with premium visual stack (atmosphere, bloom, starfield, glow)
- City markers with release counts, pulsing by activity
- Distribution arcs (waveform-modulated)
- Genre heatmap by country
- Click city → fly-to + genre panel + YouTube player
- Vibe search connected to globe navigation
- Minimap

### Phase 2 — Genre Planet MVP (4-6 weeks)
- IGTEM26 graph → Voronoi → heightmap → sphere displacement
- 5 super-genre biomes with distinct terrain + sky
- Genre territory labels
- Release particles orbiting territories
- Fly-to territory on click
- Earth ↔ Genre Planet dissolve transition
- Progressive disclosure onboarding

### Phase 3 — Discovery Engine (3-4 weeks)
- Discogs OAuth login
- Collection + wantlist import
- Personal recommendations (taste profile → content-based)
- "Highlight my collection" on both worlds
- Exclude owned + wantlisted from recommendations
- Label constellations, artist threads

### Phase 4 — Genre Architecture (4-6 weeks)
- Procedural building generator per genre biome
- InstancedMesh building pools with emissive window shader
- LOD system (3 levels)
- Genre-specific sky shaders
- Genre-specific particles (smoke/crystals/rain)

### Phase 5 — Collaborative Filtering (2-3 weeks)
- Background collection crawler (Contabo)
- Implicit ALS model training pipeline
- "Crate neighbors" feature
- Cross-genre bridge releases (gateway records)
- Hidden gems surfacing

### Phase 6 — Polish & Community (ongoing)
- Record shop layer (OSM data)
- Artist city extraction pipeline
- Drift mode (serendipity auto-navigation)
- Mystery "?" genre node
- Timeline time-warp mode
- RecordStoreAdapter plugin API (YOYAKU integration)
- MusicBrainz ID cross-reference
- Open source community launch

## 10. Open Source Strategy

- **License:** AGPL-3.0 (proven by Ampache 25y, Funkwhale)
- **Phase 1 (0-6 months):** Pure community, no YOYAKU branding
- **Phase 2 (6-9 months):** RecordStoreAdapter plugin API — any shop can integrate
- **Phase 3 (9-12 months):** YOYAKU integrates as "just one implementation"
- **Governance model:** inspired by MusicBrainz (CC0 data ethos, community editors)
- **Extension system:** inspired by Navidrome (WASM plugins)

## 11. Infrastructure

| Component | Where | Cost |
|-----------|-------|------|
| Frontend | Cloudflare Pages (free) or Contabo nginx | 0 |
| API | Contabo PM2 | Already running |
| SQLite database | Contabo | 0 |
| Redis cache | Contabo Docker | 0 |
| Collection crawler | Contabo background job | 0 |
| ALS model training | Contabo (CPU sufficient) | 0 |
| Domain | discoworld.fm (to purchase) | 87 EUR/year |
| **Total** | | **~87 EUR/year** |

## 12. Community & Open Source Strategy

### 12.1 Core Philosophy

Community-first, not monetization-first. YOYAKU integration comes LAST. The project must stand on its own as a genuinely useful open source music discovery tool that vinyl communities adopt because it's good, not because it sells records.

**Data licensing:** CC0 (like MusicBrainz/Wikidata). Contributors give freely when data stays free. Code stays AGPL-3.0.

### 12.2 Five Contributor Roles

1. **Genre Cartographers** — Define and refine genre boundaries on the map. Genre border debates (dub techno vs ambient techno) are inherently engaging and generate massive organic discussion.
2. **City Scouts** — Map real-world record shops, local scenes, city-to-genre connections. Tribal knowledge that exists nowhere as structured data.
3. **Crate Curators** — Build public "dig paths" (shareable journeys through the world). Like RYM lists (819K+ user-created) but spatial.
4. **Data Enrichers** — Add BPM, mood tags, YouTube links, sample connections, geographic origins.
5. **Visual Builders** — Contribute 3D assets for genre biomes (textures, buildings, skyboxes). Attracts the creative/dev community.

### 12.3 Governance (MusicBrainz Model)

- Anyone can propose edits to genre taxonomy, descriptions, release mappings
- Changes go to 7-day community vote
- After 50 accepted edits: auto-editor status for non-destructive edits
- Genre disputes: require citation (Ishkur, RA, Wikipedia, Discogs). No original research.
- "Mapathons" (from OSM): community events to fill underrepresented genre regions

### 12.4 Engagement (Not Gamification)

Vinyl collectors reject hollow points/badges. The 3D world IS the engagement mechanic:

- **Collection Passport**: Connect Discogs → see musical footprint on the world. Shareable "Musical DNA" card.
- **Taste Topology**: Collection visualized as terrain ("you live in the Dub Techno valleys with outposts in Detroit")
- **Gap Whisperer**: "23 minimal techno releases, 0 acid techno — here's the bridge" (map adjacency = recommendation)
- **Taste Uniqueness**: % of collection with <100 Discogs owners ("34% of your collection is rare")
- **Community thermometers**: "The Balearic coastline needs 200 more tagged releases" — cooperative, not competitive
- **Micro-contributions with visible impact**: Add a YouTube link → see it appear on the globe in real-time

### 12.5 Launch Strategy

**Pre-launch:** Ship polished demo + Discogs OAuth collection import. Purchase discoworld.fm. Create GitHub org, make repo public. Seed 6 issues (3 good-first-issue + 3 feature enhancements). CONTRIBUTING.md focused on DATA contributions (not just code).

**Week 1 — Tier 1:**
- Hacker News Show HN (Tuesday 9-11am EST): `Show HN: DiscoWorld — Open-source 3D map of 1.1M electronic releases`
- r/electronicmusic (Thursday): 30-second vibe search GIF
- Three.js Discourse: technical showcase post

**Week 2 — Tier 2:**
- Product Hunt (separate week from HN)
- r/vinyl + r/VinylCollectors: "find your next vinyl dig by genre, era, and vibe"
- Pitch RA editorial team (features@ra.co)

**Week 3+ — Tier 3:**
- TikTok/IG video clips (genre fly-throughs, timeline scrubbing)
- Mastodon/Fediverse (natural fit for open source ethos)
- Technical blog: Discogs data pipeline deep-dive

**Early advocates to recruit:**
- Ishkur (spiritual ancestor of the genre map — contact him)
- Discogs power users (10K+ collection)
- Resident Advisor contributors
- University music technology departments (ISMIR conference community)
- Record shop staff and label owners as genre shepherds

### 12.6 Sustainability (Months 6-12)

- MetaBrainz model: free API for non-commercial, paid tiers for commercial use
- GitHub Sponsors / Open Collective with transparent finances
- DiscoWorld's spatial genre taxonomy has commercial value for recommendation engines
- RecordStoreAdapter plugin API = commercial bridge (YOYAKU = "just one implementation")

## 13. Key References

### Technical
- [WorldMonitor (koala73)](https://github.com/koala73/worldmonitor) — Globe architecture, dual rendering, data pipeline
- [globe.gl](https://github.com/vasturiano/globe.gl) — 3D globe library
- [IGTEM26](https://github.com/eskoNBG/IGTEM26) — 251 electronic genres, 502 edges
- [Red Blob Games Polygonal Map Generation](http://www-cs-students.stanford.edu/~amitp/game-programming/polygon-map-generation/) — Voronoi terrain pipeline
- [Implicit](https://github.com/benfred/implicit) — ALS collaborative filtering
- [Music Galaxy](https://cprimozic.net/blog/building-music-galaxy/) — 70K artists in 3D browser

### Visual
- [GitHub Globe](https://github.blog/engineering/engineering-principles/how-we-built-the-github-globe/) — Premium globe visual stack
- [Rototu Procedural City](https://github.com/Rototu/procedural-skyscraper-city-generator-and-shader) — Building generation
- [SynthCity](https://discourse.threejs.org/t/synthcity-an-infinite-procedural-cyberpunk-city/59887) — Procedural cyberpunk

### UX
- [Auralist: Serendipity in Music Recommendation](https://www.researchgate.net/publication/221519984_Auralist_Introducing_serendipity_into_music_recommendation)
- [Music Galaxy UX lessons](https://cprimozic.net/blog/graph-embeddings-for-music-discovery/)
- [Musicmap](https://musicmap.info/) — Genre continent concept

### Data
- [Discogs API Documentation](https://www.discogs.com/developers)
- [Discogs Data Dumps](https://data.discogs.com/)
- [@lionralfs/discogs-client](https://www.npmjs.com/package/@lionralfs/discogs-client) — OAuth + collection
- [Musicmap JSON](https://musicmap.info/master-genrelist.json) — Super-genre groupings
