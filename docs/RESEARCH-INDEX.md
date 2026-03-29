# DiscoWorld Research Index

## Documents

| File | Contents | Status |
|------|----------|--------|
| `electronic-music-taxonomy.json` | Genre bible: 17 genres, 50 sub-genres, 15 neighbors, 25 cities, 6 decades | Done |
| `01-electronic-music-history.md` | Complete history — 6 eras, 20+ cities, branch genealogy, 3D visuals per scene | Done |
| `02-visual-culture.md` | Visual identity per genre — colors, aesthetics, key artists, audio-to-visual mapping | Done |
| `03-world-design.md` | Genre-to-world mapping — volcanic atoll, 10 biomes, terrain/sound mapping, temporal evolution | Done |
| `04-tech-stack.md` | Stack decisions — Vite+React+R3F+Zustand, no deck.gl/Next.js, benchmarks, mobile, deploy | Done |
| `05-3d-web-inspiration.md` | Reference sites — Lusion, Music Galaxy, GitHub Globe, procedural generators, design rules | Done |
| `06-features-ecosystem.md` | Features: landing page, in-store sessions, DJ charts, supply chain pipeline, collection passport, YOYAKU flywheel | Done |
| `07-open-source-strategy.md` | AGPL-3.0, WordPress model, phased YOYAKU integration, fork risk, community trust | Done |
| `08-innovative-features.md` | Vibe search, crate neighbors, taste distance, DJ transitions, gamification, MVPs | Done |
| `09-discogs-data-model.md` | Discogs dump schema, styles taxonomy, data pipeline design | Pending |
| `10-architecture-plan.md` | Final architecture plan — consolidation of all research | Pending |

## External Data Sources

| Source | Location | Status |
|--------|----------|--------|
| Discogs March 2026 - Labels | `data/discogs-dump/discogs_20260301_labels.xml.gz` (83 MB) | Downloaded |
| Discogs March 2026 - Artists | `data/discogs-dump/discogs_20260301_artists.xml.gz` (460 MB) | Downloaded |
| Discogs March 2026 - Masters | `data/discogs-dump/discogs_20260301_masters.xml.gz` (574 MB) | Downloaded |
| Discogs March 2026 - Releases | `data/discogs-dump/discogs_20260301_releases.xml.gz` (10.2 GB) | Downloading |
| Ishkur's Guide Dataset | `data/ishkur-dataset/` (167 genres, 353 links, 11K tracks) | Cloned |
| IGTEM v4.0 (community fork) | Repo not found (eskoNBG/IGTEM26) | Unavailable |
| cosine.club API | API key needed | To setup |

## Key Decisions (resolved)

- [x] **World structure:** Volcanic atoll (ring + archipelago). Dual view: Earth Mode + Genre World
- [x] **3D engine:** React Three Fiber (R3F) + drei + custom shaders
- [x] **Framework:** Vite + React (NOT Next.js — WebGL can't SSR)
- [x] **State:** Zustand (R3F standard)
- [x] **deck.gl:** Skip (clunky integration, custom shaders give more control)
- [ ] UMAP positioning: metadata-only vs audio embeddings vs hybrid
- [ ] Open source boundary: what's open vs proprietary (defined conceptually, not implemented)
- [ ] Domain: discoworld.fm (to purchase — 87€/year)
- [ ] Tile format: PMTiles (static) vs Martin (dynamic) — for Earth Mode

## Ishkur Scenes (potential continent mapping)

27 scenes from Ishkur v3 dataset — these could map to DiscoWorld territories:
Ambient, Bass, Breakbeat, Chill Out, Chiptune, Downtempo, Drum n Bass, Electro, Eurodisco, Europop, Eurotrance, Eurotrash, Garage/Deep House, Hard Dance, Hardcore, Hip Hop, House, Industrial/Goth, Intelligent Dance Music, Pioneers, Progressive, Psy Trance, Tech House, Techno, Trance, UK Garage, Urban
