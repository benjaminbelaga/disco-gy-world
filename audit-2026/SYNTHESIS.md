# DiscoWorld Mega-Audit — Synthesis & Refactor Plan
*Generated 2026-04-17. Source: 6 parallel research agents (A–F). Total audit ~1400 lines in sibling files.*

---

## Executive summary

Ben's visual brief — *"moins dark, pas pitch-black, continents avec identité, pas clown-colour, plus d'espace"* — is backed by unanimous agent consensus:

1. **Layout is the structural bug.** Agent D discovered the current "3D" scene is actually 2D (`y=0` for all 166 genres). `WORLD_RADIUS=48` plus near-zero scene gravity produces a tight blob at origin with ~70 % void ratio in the accessible disc. Fixing this alone solves 60 % of the visual brief.
2. **Black void is a style anti-pattern, not a bug.** Every single reference (zig-zag.fm cream, Music Galaxy nebula, Radiooooo Mapbox) avoids pure black. Agent C recommends **Night Atlas** (warm dark `#1c1917`) as the lowest-migration fix that preserves the existing bloom/lighting stack.
3. **Labels are the readability bug.** Agent B mapped the current stack (36 SDF + 36 DOM Html labels, always-on, no LOD, wrong font, invisible 22 %-alpha decade ghosts) and prescribed a 4-tier hierarchy with distance-based fade and a cheap NDC-bbox collision pass.
4. **Perf headroom is large and mechanically recoverable.** Agent E found ~500 individual `<line>` draw calls (should be 2 LineSegments) and 80+ per-item `useFrame` subscribers. P0+P1 fixes project +30–60 FPS on integrated GPUs, double mobile FPS.
5. **We're alone in 3D.** Agent F confirmed no active 2025-2026 3D music explorer competes with DiscoWorld. Zig-zag.fm is 2D. Everynoise is zombie (Glenn McDonald left Spotify). Our unique moat: 3D triad + Discogs/YOYAKU OAuth + dig-path URL encoding + real record shop anchoring.

**Agent reports:**
- `AGENT-A-design-references.md` — visual refs + mood boards
- `AGENT-B-readability.md` — label system + 8 concrete file:line edits
- `AGENT-C-palette.md` — 4 palettes, recommends Night Atlas
- `AGENT-D-spatial-layout.md` — UMAP + anchor pipeline, 3-day eng
- `AGENT-E-performance.md` — 12 ranked perf fixes with file:line anchors
- `AGENT-F-competitor-matrix.md` — feature matrix + strategic moat

---

## Cross-agent decisions (reconciling contradictions)

| Topic | Agent A | Agent C | Decision |
|---|---|---|---|
| Background | Cream OR nebula (two bets) | Night Atlas warm dark `#1c1917` | **Night Atlas** — lowest migration cost, preserves bloom, brand-aligned with YOYAKU gold `#c4956a`. Cream/aurora are viable second-phase pivots. |
| Color per-genre | Noise-varied (Music Galaxy) + gold accent | Per-continent accents (5 hues) | **Both.** Noise-varied hue assigned by 3D-position-over-noise; 5 continent accents override noise at continent level. Gold reserved for user's data. |
| Label tech | HTML overlay OR SDF LOD | (out of scope) | **SDF + Billboard** for continents (Agent B tier 0-3). HTML reserved for interactive pills only. |

---

## PR plan — 5 sequential shipments, smallest-win-first

Each PR is independently mergeable and delivers visible user value. Target: one PR per session.

### PR #1 — Night Atlas palette swap (≈1 day)
**Scope:** color constants only, no geometry changes.

- Replace `scene.background = new THREE.Color(0x000000)` → `0x1c1917` in `GenreWorld.jsx`, `GenrePlanet.jsx`
- Add `THREE.Fog(0x1c1917, 10, 80)` to each scene
- Boost emissive intensity +20 % on genre spheres to compensate for bloom against non-black bg
- Swap overlay text color `#ffffff` → `#f5f5f4` across CSS
- Add CSS tokens file `packages/web/src/tokens/palette.css` with Stone 900 + YOYAKU gold + sand + terracotta + bronze + sage
- Ground plane subtle `#292524` at `y=-5`, opacity 0.6

**Success criteria:**
- No regression in E2E (re-run `/tmp/dw-health.js` after adjusting CF workaround)
- Visual diff: screenshot before/after on 3 viewports
- Bloom still visible on active continent

**File:line anchors:** `GenreWorld.jsx:32,735,709`, `GenrePlanet.jsx`, `App.css`, `index.css`

### PR #2 — P0 perf wins (≈1 day)
Three uncontroversial perf refactors from Agent E. Zero visual change, pure FPS gain.

- **Merge `GenreLinks` + `SceneConnections`** into 2 `THREE.LineSegments` with single BufferGeometry (`GenreWorld.jsx:506,686`). Drops ~500 draw calls to 2. Expected +12–20 FPS.
- **Add drei `<PerformanceMonitor>`** at `App.jsx:141` with auto-DPR/bloom gate for FPS <45. Expected +15–30 FPS on weak GPUs.
- **Downgrade `GenreWorldBuildings` material** from `meshStandardMaterial` → `meshLambertMaterial` (`:91,109,127`). Expected +4–8 FPS on mobile.
- **Dynamic-import `@react-three/postprocessing`** via `lazy()` — saves 397 KB gzip on mobile first-paint (`App.jsx:5`).

**Success criteria:** FPS counter via `PerformanceMonitor` shows ≥45 FPS on M1 air, ≥30 FPS on iPhone 12.

### PR #3 — LOD label system (≈1–1.5 day)
Agent B's 4-tier hierarchy. Single biggest readability win.

- Ship Space Grotesk woff files in `packages/web/public/fonts/`
- Create `tokens/labels.js` with `LABEL_TOKENS` (tiers 0-4, outline, minPixelSize)
- Enrich genres in `useStore.js:setGenres` with `tier`, per-scene centroid, representative genre
- Rewrite `GenreLabels` in `GenreWorld.jsx:400-430` → split into Primary/Secondary/Tertiary components
- Replace `BiomeLabels` HTML with SDF `<Text>` (tier 0), wrap in `<Billboard lockY>`, fix "primary=closest-to-centroid" bug (`:786`)
- Replace `DecadeLabels` HTML with `<Text>` at fontSize 3.0, opacity 0.35, `rotation={[-PI/2,0,0]}` (flat map cartouche)
- Add `LabelCollisionManager`: single `useFrame` walks refs, NDC bbox collision, `.visible` toggling
- Bonus: press `L` to toggle LOD debug HUD

**Success criteria:**
- Continent labels readable at camera dist 50, fade out at dist <30
- No two tier-1+ labels overlap >12 px after collision pass
- Font matches app UI (Space Grotesk everywhere)

### PR #4 — Noise-varied color + gold user accent (≈0.5 day)
Agent A pattern 2. Solves "clown-colour" directly.

- Replace per-genre random colors with `simplex3D(x, y, z) → HSL` mapping
- Override noise hue for 5 continent accents (Stone 900 / Gold / Terracotta / Ink / Moss)
- Reserve `#c4956a` gold for: current city, active genre, user's dig-path trail, user's favorites
- Fallback to scene color for genres without noise coords (shouldn't happen post-PR #5)

**File:line anchors:** `GenreWorld.jsx:colorForGenre`, `useStore.js`

### PR #5 — Spatial layout rebuild (≈3 days) ⚠ biggest change
Agent D's full pipeline. Ship BEHIND a feature flag (`?layout=v2`) first, promote after 1 week of Ben's testing.

- New Python pipeline:
  - `packages/pipeline/build_genre_embeddings.py` (text + node2vec + co-tag hybrid)
  - `build_genre_layout.py` (UMAP n_neighbors=8, spread=2.0, cosine)
  - `shape_continents.py` (anchor-pin 8-12 canonical hubs, force relax, Lloyd, concave hull)
  - `compute_altitude.py` (y axis from trackCount/biome/BPM, max_height=20)
- `config/genre_anchors.yaml` — editorial seed positions (Detroit techno, Chicago house, UK garage, …)
- Refactor existing `genre_world_generator.py` into an orchestrator that calls the 4 phases
- `scripts/rebuild-world.sh` — end-to-end pipeline runner
- Client: render continent polygons as ground decals in `GenreWorld.jsx`
- Expand `WORLD_RADIUS` 48 → 120, `scene_gravity` 0.003 → 0.03

**Success criteria** (measurable):
| Metric | Current | Target |
|---|---|---|
| World radius | 48 | 120 |
| Void ratio (in bounding disc) | ~70 % | 50–60 % |
| Scene intra-cluster / inter-cluster dist ratio | ≈0.9 | **<0.45** |
| y variance | 0 | ≥3× max sphere radius |
| Anchored hub genres | 0 | 8–12 |

---

## Non-blocking follow-ups (backlog)

From Agent E (P2 + P3):
- `frameloop='demand'` + `<AdaptiveEvents>` for 70 % idle GPU save
- Dispose WebGL context on view switch (prevents Safari multi-context crash)
- `buildingSystem.getSurfacePoint` analytical replacement (removes 100 ms territory-click stutter)
- Planet ocean shader octaves 3 → 1 (+8–15 FPS on planet view)
- Memoize inline `<ringGeometry>` + `<sphereGeometry>` allocations

From Agent F (strategic):
- Era-first time machine (Radiooooo pattern) — make year/decade a primary axis
- Editorial curator islands — YOYAKU staff-promoted releases as named islands
- ML audio-similarity (cosine.club pattern) — needs embeddings pipeline
- Paid tier: drift-mode-24/7 or unlimited dig paths behind €3/mo

From Agent B (bonus):
- LOD debug HUD (press `L`)

---

## Known test-harness issue (not a prod bug)

The E2E harness at `/tmp/dw-health.js` hits Cloudflare bot challenges on URL variants (not the bare `/`). Symptoms: `EarthGlobe: failed to load data SyntaxError: Unexpected token '<'` — CF returns HTML challenge for a `/data/*.json` fetch, which isn't JSON. **Prod is unaffected for real users.** Before depending on E2E for regression coverage, either (a) allow Playwright UA in CF, (b) run the tests against a Vite preview server locally, or (c) add a CF bypass header for the test runner's IP.

---

## Next action

**Ship PR #1 first.** Palette swap is pure color constants — zero geometry risk, maximum perceived improvement. Ben can see the direction in 30 seconds. If he redirects to cream/aurora instead, we swap the hex codes, no refactor needed.

PRs #2–#4 can ship in any order against `main` after PR #1 lands. PR #5 (layout rebuild) should be last and gated behind `?layout=v2` for Ben to A/B visually before promotion.
