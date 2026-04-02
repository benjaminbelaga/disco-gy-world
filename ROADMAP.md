# DiscoWorld Roadmap

## Completed (v2.0)

### Phase 0: Data Foundation
- [x] Taxonomy bridge (Discogs styles ↔ Ishkur genres)
- [x] Style co-occurrence matrix (4.87M releases)
- [x] Content-based similarity index (cosine on style+label vectors)
- [x] Unified SQLite database
- [x] FastAPI endpoints (recommendations, releases, genres)

### Phase 1: Earth Globe
- [x] globe.gl with Fresnel atmosphere, starfield, bloom
- [x] 35 city markers with pulsing activity
- [x] Distribution arcs (waveform-modulated, cyan)
- [x] Hexbin heatmap (release density by country)
- [x] CityPanel sidebar with YouTube
- [x] SVG minimap with click-to-fly
- [x] Vibe search → globe navigation
- [x] Layer toggle controls

### Phase 2: Genre Planet
- [x] Voronoi terrain from genre graph
- [x] 166 genre territories on procedural sphere
- [x] 12 biome types with distinct terrain
- [x] Heightmap generation (BPM=altitude)
- [x] 3-way view transition (crossfade, GPU pause)

### Phase 3: Discovery Engine
- [x] Discogs auth (token-based MVP)
- [x] Collection + wantlist sync
- [x] Personal recommendations (content-based, hidden gems)
- [x] Taste profile (diversity, rarity, gap analysis)
- [x] Collection Passport frontend
- [x] Recommendation panel

### Phase 4: Genre Architecture
- [x] Procedural building generator (25 archetypes, 5 biomes)
- [x] Emissive window shader
- [x] InstancedMesh with LOD
- [x] Genre-specific sky shaders (7 atmospheres)
- [x] Genre-specific particles (smoke, fireflies, sparkles, sparks, beams)

### Phase 5: Collaborative Filtering
- [x] Collection crawler (snowball, privacy-safe)
- [x] ALS matrix factorization (Implicit)
- [x] Crate neighbors API
- [x] Hybrid recommendations (content + collaborative)
- [x] Cross-genre bridge detection

### Phase 6: Polish & Launch
- [x] Drift mode (serendipity auto-navigation)
- [x] Mystery "?" genre node
- [x] Progressive disclosure onboarding
- [x] README, CONTRIBUTING.md, LICENSE (AGPL-3.0)
- [x] Data license (CC0)
- [x] Issue templates + seed issues

## Up Next

### Community Building
- [ ] Register Discogs OAuth app (multi-user)
- [ ] Purchase discoworld.fm domain
- [ ] Create GitHub org `discoworld`
- [ ] Transfer repo to org
- [ ] Show HN launch
- [ ] Contact Ishkur for genre shepherd role
- [ ] Run first community mapathon

### Technical Improvements
- [x] Code-splitting (Vite dynamic imports per view) — 514 kB initial, -81%
- [x] Mobile touch controls optimization — bottom sheets, bloom off, double-tap zoom
- [x] Dig paths (shareable curated journeys) — URL base64 sharing, CatmullRom curves
- [x] Label constellations — gold connection lines between genres sharing a label
- [x] Artist threads visualization — CatmullRom timeline blue→amber, fly-to
- [x] Collection highlight (gold torus rings, amber ripples, TasteTopology PNG)
- [x] Full Discogs dump pipeline (all 4.87M releases in DB, 944 MB)
- [x] Real audio reactivity (Web Audio API) — bass→scale, beat→particles, mic input
- [x] Search-as-you-type (Cmd+K fuzzy search, 697K artists, 361K labels, keyboard nav)
- [x] URL deep linking (?view=genre-world&genre=techno, Share button)
- [x] PWA offline mode (service worker, 23 precache entries, install prompt)
- [x] Artist city enrichment (280+ artist mappings, 120+ label mappings, city API)
- [ ] WebGPU renderer (Three.js TSL)
- [ ] Strudel live coding integration (pattern generator built, needs UX polish — disabled for now)
- [x] Accessibility (keyboard nav, screen reader labels, reduced motion)
- [x] Biome soundscape engine (procedural ambient audio, 13 biome drones, Web Audio API)
- [x] Social sharing (OG image generator, Web Share API, deep link URLs)
- [x] Curated dig paths (8 preset journeys: Detroit→Berlin, Birth of House, UK Bass, etc.)
- [x] Community stats in UI (have/want/ratings on release cards, rankings endpoint)
- [x] Comprehensive test suite (346 tests: 103 API, 63 pipeline, 137 frontend, 43 Playwright E2E)

### Data Enrichment
- [x] Artist city extraction (curated mappings + DB scanning)
- [x] Label address extraction (30K labels, 81 cities from Discogs dump)
- [x] OSM record shop dataset (7,121 shops, vinyl/records tags, 1,822 vinyl-flagged)
- [x] MusicBrainz ID cross-reference (batch pipeline with cover art, 80% match rate)
- [x] Discogs community have/want enrichment via API (pipeline + rankings endpoint)

### Open Source Ecosystem
- [x] RecordStoreAdapter plugin API (interface, registry, Discogs + YOYAKU adapters, docs)
- [x] Community genre editing system (propose, vote, auto-approve/reject thresholds)
- [x] MetaBrainz-style edit voting (3-vote threshold, duplicate prevention, closed-edit protection)
- [ ] GitHub Sponsors / Open Collective
- [x] Contributor recognition system (leaderboard, profiles, point system, 5 contribution types)
- [x] Discogs OAuth 1.0a multi-user (configurable, token fallback, session management)
- [x] Show HN preparation (demo tour, seed issues, polished CONTRIBUTING.md)
