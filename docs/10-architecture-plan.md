# DISCOWORLD.FM — Architecture Plan v2 (Final)

> The open source 3D musical world that makes Zig-Zag, Radiooooo, and Every Noise obsolete.

---

## VISION

A 3D interactive planet where every music release ever pressed on vinyl has a position. Navigate by genre, geography, and time. Connect your Discogs collection to see your musical footprint. Describe a vibe in words and land in the right neighborhood. Find your crate neighbors. Watch genres emerge like cities growing over decades.

**Open source core. Community-driven. Subtly connected to YOYAKU's ecosystem.**

---

## THE TWO UNIVERSES

### Universe 1 — Earth Mode
Real world map. Music mapped to where it originates.
- Detroit techno as glowing cluster on Michigan
- Berlin minimal as dense node on Germany
- Chicago house, London dubstep, Kingston dub
- Data: Discogs label country + our city→genre mapping (25 cities)
- Timeline slider: watch scenes emerge and die across decades
- Tech: MapLibre GL JS with 3D terrain + Three.js overlays

### Universe 2 — DiscoWorld (Genre Planet)
Fictional planet. Continents ARE genres. A volcanic atoll ring.
- Inner coastline = 1960s origins. Outer edge = present day
- Genre families = archipelago clusters connected by land bridges
- The Source Sea = ambient/drone (underwater realm)
- Buildings = releases. Height = release count. Style = genre aesthetic
- Timeline: buildings grow like SimCity as you scrub through decades
- Tech: React Three Fiber + InstancedMesh + custom shaders

### Switch: Earth ↔ DiscoWorld
Toggle button with smooth camera transition (GSAP). Same data, two projections.

---

## TECH STACK (Final)

```
Frontend:  Vite + React + React Three Fiber + drei + Zustand
3D:        Three.js (InstancedMesh + custom shaders + selective bloom)
Maps:      MapLibre GL JS (Earth Mode only)
State:     Zustand (camera, timeline, filters, playback, selection)
Audio:     YouTube IFrame API (Phase 1) → Apple MusicKit JS (Phase 6)
Backend:   FastAPI (Python)
Database:  PostgreSQL + pgvector + PostGIS
Tiles:     Martin (Rust) or PMTiles (static)
ML:        UMAP (Python) + Essentia/cosine.club for audio embeddings
Cache:     Redis
Deploy:    Self-hosted + Cloudflare R2 CDN for assets
```

**Why these choices:** See `04-tech-stack.md` for full rationale. Key: no deck.gl (clunky), no Next.js (WebGL can't SSR), R3F for declarative 3D + React UI.

---

## DATA PIPELINE

```
Discogs Monthly XML Dump (CC0, ~10 GB compressed)
        ↓
Streaming XML Parser (Python lxml.iterparse)
        ↓
PostgreSQL (normalized: releases, artists, labels, genres, styles)
        ↓
Genre Classification (Discogs styles + Ishkur mapping + our taxonomy)
        ↓
Embedding Generation:
  Option A: Metadata vectors (genre + era + country + label + credits)
  Option B: Audio embeddings via cosine.club API (1.15M electronic tracks)
  Option C: Hybrid (A + B weighted)
        ↓
UMAP Projection → 2D coordinates (for DiscoWorld planet layout)
        ↓
Coordinate → PostGIS geometry (UMAP x,y mapped to lng,lat space)
        ↓
Vector Tiles (Martin from PostGIS, or pre-built PMTiles)
        ↓
Heightmap Generation (release density → terrain elevation)
        ↓
Frontend loads tiles + heightmaps + plays YouTube
```

### Data Sources

| Source | Data | Update Frequency | License |
|--------|------|-----------------|---------|
| Discogs Data Dumps | Releases, artists, labels, masters | Monthly | CC0 |
| Discogs API | Want/have counts, marketplace, collections | Real-time (60 req/min) | Free |
| Ishkur's Guide Dataset | 167 genres, 353 connections, 11K tracks | Static (2019) | Community |
| Our Genre Taxonomy | 17 genres, 50 sub-genres, 25 cities | Maintained by us | Proprietary |
| cosine.club API | Audio embeddings for 1.15M electronic tracks | On-demand | Free tier |
| Bandcamp/Beatport | Trending/charts (scraping) | Weekly | Scraping |

---

## FEATURES BY PHASE

### Phase 1 — The Map (Months 1-3)

**Goal:** A beautiful, functional 3D world you can explore and play music from.

| Feature | Priority | Effort |
|---------|----------|--------|
| DiscoWorld globe (3D planet with genre biomes) | P0 | 3 weeks |
| Genre territories with color-coded biomes | P0 | 1 week |
| Zoom levels (planet → continent → district → release) | P0 | 2 weeks |
| YouTube playback (click release → play) | P0 | 1 week |
| Genre/style filters | P1 | 1 week |
| Country filter | P1 | 3 days |
| Timeline slider (1960-2026) | P1 | 2 weeks |
| Building growth animation (shader-based) | P1 | 1 week |
| **"Describe a vibe"** natural language search | P1 | 1 week |
| Earth Mode (real geography) | P2 | 2 weeks |
| Earth ↔ DiscoWorld toggle transition | P2 | 1 week |

**Launch target:** Reddit (r/TheOverload, r/vinyl, r/webdev), Hacker News.

### Phase 2 — Your Collection (Months 3-5)

| Feature | Priority | Effort |
|---------|----------|--------|
| Discogs OAuth login | P0 | 3 days |
| Collection import + map overlay | P0 | 1 week |
| "Your Musical DNA" stats (genres, countries, decades) | P1 | 1 week |
| Shareable "DiscoWorld Passport" card | P1 | 3 days |
| **Crate Neighbors** (find similar collectors) | P1 | 1 week |
| **Taste Distance** (shareable metric) | P2 | 3 days |
| Playlists (create, save, share) | P2 | 1 week |
| Recommendations based on collection gaps | P2 | 1 week |

### Phase 3 — Community (Months 5-7)

| Feature | Priority | Effort |
|---------|----------|--------|
| User contributions (metadata corrections) | P0 | 2 weeks |
| Genre connection tagging ("influenced by", "samples") | P1 | 1 week |
| "Gem" a release (community highlighting) | P1 | 3 days |
| Explorer badges / gamification | P2 | 1 week |
| "Year in DiscoWorld" annual recap | P2 | 1 week |
| DJ transition suggestions (BPM + genre bridging) | P2 | 1 week |

### Phase 4 — Dynamic Content (Months 7-9)

| Feature | Priority | Effort |
|---------|----------|--------|
| Landing page: trending releases (Discogs dump diff) | P0 | 1 week |
| Landing page: "Most wanted" by genre | P0 | 3 days |
| DJ Charts (from in-store session tracklists) | P1 | 2 weeks |
| In-store session tracklist → map visualization | P1 | 2 weeks |
| "Hot this week in Berlin Techno" dynamic sections | P1 | 1 week |
| QR code → release on map (for physical stores) | P2 | 3 days |

### Phase 5 — Record Store Plugin (Months 9-12)

| Feature | Priority | Effort |
|---------|----------|--------|
| `RecordStoreAdapter` interface (open, documented) | P0 | 1 week |
| Mock store reference implementation | P0 | 3 days |
| "Available at [Store]" badge on releases | P0 | 3 days |
| Store inventory sync API | P1 | 1 week |
| YOYAKU adapter (first real implementation) | P1 | 1 week |
| "New arrivals at [Store]" notifications | P2 | 3 days |

### Phase 6 — YOYAKU Deep Integration (Month 12+)

| Feature | Priority | Effort |
|---------|----------|--------|
| "Currently pressing" (Objects manufacturing data) | P1 | 1 week |
| "Arriving this week" (YYD distribution data) | P1 | 1 week |
| In-store session → auto-order pipeline | P2 | 2 weeks |
| Apple Music / Spotify playback (MusicKit JS) | P2 | 2 weeks |
| Barcelona store physical-digital loop | P3 | Ongoing |

---

## OPEN SOURCE STRATEGY

### License: AGPL-3.0
Prevents closed forks, encourages contributions. See `07-open-source-strategy.md`.

### GitHub Organization: `discoworld`
Not `benjaminbelaga`. Not `yoyaku`. Neutral.

### Repos
```
discoworld/discoworld     — Main app (AGPL-3.0)
discoworld/pipeline       — Data pipeline (AGPL-3.0)
discoworld/contrib        — Contribution SDK (MIT)
discoworld/docs           — Documentation (CC BY 4.0)
```

### Founder Transparency
README states: "Created by Ben Belaga, who also runs YOYAKU records in Paris."
Authenticity > secrecy. The WordPress/Mullenweg model.

### Integration Timeline
- **Months 0-6:** Zero commerce. Pure community.
- **Months 6-9:** Store plugin API announced + documented (generic, open).
- **Months 9-12:** YOYAKU integrates as "just one implementation."
- **Month 12+:** YOYAKU's vertical data makes its integration naturally superior.

---

## WORLD DESIGN SUMMARY

### Biome Map

| Territory | Genre Family | Visual | Colors |
|-----------|-------------|--------|--------|
| **Techno Massif** | Techno + sub-genres | Basalt mountains, brutalist bunkers, thunderstorms | Grey, black, cyan, hazard yellow |
| **House Plains** | House + sub-genres | Golden savanna, open pavilions, warm lights | Orange, gold, brown, red |
| **Ambient Depths** | Ambient, drone | Underwater, bioluminescent caves | Deep blue, teal, soft glow |
| **Trance Highlands** | Trance, psytrance, goa | Crystal spires, aurora sky, fractal trees | Purple, teal, neon green |
| **Jungle Canopy** | DnB, jungle | Massive trees, canopy cities, rain | Dark green, gold, red |
| **Industrial Wasteland** | Industrial, EBM, noise | Volcanic flats, sulfur vents, factories | Rust, gunmetal, dark red |
| **Disco Riviera** | Disco, nu-disco, italo | Coastal resort, mirror-ball lighthouses | Chrome, pastels, sunset |
| **Dubstep Rift** | Dubstep, bass | Deep canyon, purple-lit, bass tremors | Deep purple, dark blue |
| **IDM Crystalline** | IDM, glitch | Geometric crystals, algorithmic architecture | White, neon accents, glitch |
| **Minimal Garden** | Minimal, microhouse | Zen rock garden, sparse, clean | White, grey, single accent |

### Terrain-to-Sound Mapping

| Musical Property | Terrain Property |
|---|---|
| BPM | Elevation (70=sea level, 170+=volcanic summits) |
| Energy/Darkness | Temperature + weather |
| Harmonic complexity | Vegetation density |
| Release volume | Territory area + building density |
| Influence | Rivers connecting territories |

### Time Animation
Shader-based: each building has `birthYear` attribute. Vertex shader: `smoothstep(birthYear, birthYear+2, currentYear) * targetHeight`. Scrubbing = 1 uniform update, entire world responds at 60fps.

---

## HOSTING & COSTS

| Resource | Cost | Notes |
|----------|------|-------|
| Domain (discoworld.fm) | 87€/year | To purchase |
| Hosting | 0€ incremental | Self-hosted server has capacity |
| Discogs data | 0€ | CC0 dumps, free API |
| cosine.club API | 0€ | Free tier |
| YouTube API | 0€ | Free quota |
| CDN (Cloudflare R2) | ~5€/month | For textures, tiles, assets |
| **Total Year 1** | **~150€** | Nearly free to operate |

---

## IMMEDIATE NEXT STEPS

### This Week
- [ ] Purchase discoworld.fm domain
- [ ] Create GitHub org `discoworld` (private repos for now)
- [ ] Initial commit with docs/ and data pipeline skeleton
- [ ] Wait for releases dump to complete (~10.2 GB)
- [ ] Write Discogs XML → PostgreSQL ingestion script

### Week 2
- [ ] Ingest Discogs data into PostgreSQL (releases, artists, labels)
- [ ] Filter electronic music subset (~500K releases)
- [ ] Generate metadata embeddings + UMAP coordinates
- [ ] Create first heightmap from release density
- [ ] Scaffold Vite + React + R3F project

### Week 3-4
- [ ] Prototype: render DiscoWorld globe with genre biomes
- [ ] Color-coded territories from our taxonomy
- [ ] Zoom levels (planet → continent → district)
- [ ] YouTube playback integration
- [ ] First screenshot for README

### Month 2
- [ ] Timeline slider + building growth animation
- [ ] "Describe a vibe" search
- [ ] Earth Mode + toggle
- [ ] Genre/country/era filters
- [ ] Internal testing

### Month 3
- [ ] Discogs OAuth + collection import
- [ ] "Your Musical DNA" stats
- [ ] Shareable passport card
- [ ] **Public launch: Reddit + Hacker News**

---

## SUCCESS METRICS

| Metric | Target (Month 3) | Target (Month 6) | Target (Month 12) |
|--------|-------------------|-------------------|---------------------|
| Monthly visitors | 10K | 50K | 200K |
| Discogs collections connected | 500 | 5K | 20K |
| Releases mapped | 500K | 1M | 3M |
| GitHub stars | 100 | 1K | 5K |
| Community contributions | 50 | 500 | 2K |
| Record stores integrated | 0 | 0 | 5 (incl. YOYAKU) |
| Reddit/HN mentions | 1 launch post | 5 | 20 |

---

## THE MOAT

Nobody else can replicate this because:

1. **Data chain:** Tracklist plays × Discogs catalog × store inventory × manufacturing data = only YOYAKU has all 4
2. **Community:** Collection data + contributions + crate neighbor graph = network effect
3. **Curation:** Genre taxonomy + biome mapping + visual design = editorial moat
4. **Vertical integration:** Pressing (Objects) → Distribution (YYD) → Retail (YOYAKU) → Discovery (DiscoWorld) = the full chain

**DiscoWorld is the front door to the YOYAKU universe. But the door is open source, beautiful, and genuinely useful — even without YOYAKU.**
