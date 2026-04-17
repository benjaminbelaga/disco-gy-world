# AGENT E — 3D Rendering Performance Audit

**Scope:** `world.yoyaku.io` (React 19 + R3F + Three.js + globe.gl). Date 2026-04-17.
**Focus:** scene-graph profiling (not bundle — see Agent B). Three views: `genre` (R3F Canvas), `earth` (globe.gl raw Three), `planet` (raw Three).

---

## 1 — Per-component scene-graph profile

### 1.1 `GenreWorld.jsx` (997 lines — biggest offender)

`<GenreWorld>` is a single `<group>` composed of ~16 sub-components, **every one currently mounted simultaneously** even when the user only sees part of the UI. Below is a mesh/draw-call inventory assuming `genres.length = 166`, `releases = 500` (mobile) / unlimited (desktop), `links ≈ 200`.

| Component | File:line | Meshes/frame | Instanced? | Geo reuse | useFrame | Notes |
|---|---|---|---|---|---|---|
| `Ground` | L30-41 | 1 | — | inline `<planeGeometry>` → re-created each render | no | 300×300 plane, MeshStandard w/ metalness |
| `Grid` | L44-51 | 1 (LineSegments via gridHelper) | — | inline | no | 80×80 grid lines (~6.4k line verts) |
| `GlowRings` | L54-107 | **N_scenes individual meshes** (~12) | NO | `<ringGeometry>` inline per ring → **re-created every render of GlowRings** | yes, 60 Hz (unthrottled) | `ringGeometry(inner, outer, 64)` not memoized |
| `CollectionRings` | L114-169 | 1 instanced | YES (`_ring` module const) | good | yes (60 Hz) | fine |
| `GenreWireframes` | L172-236 | 1 instanced (166) | YES | shared `_wireframeSphere` | yes (60 Hz) | wireframe `meshBasicMaterial` + instanceColor — OK |
| `SelectionRing` | L241-272 | 1 | — | shared `_selectRing` | yes (60 Hz) | fine |
| `GenreInstances` | L275-373 | 1 instanced (166) | YES | shared `_sphere` | yes (60 Hz) | **`meshStandardMaterial` w/ vertexColors** — shader-heavy vs MeshBasic/Lambert |
| `GenreWorldBuildings` | GWB.jsx L85-136 | 3 instanced (box/cyl/cone, up to 2000/500/500 = **3000**) | YES | module-level | no (static after mount) | MeshStandard x3 — heavy but static |
| `HoverTooltip` | L376-397 | 1 `<Html>` | — | — | no | DOM, cheap |
| `GenreLinks` | L474-518 | **1 individual `<line>` per link** (up to ~200) | NO | `BufferGeometry` re-created in `useMemo` every `year/activeSlug/hoveredSlug` change | no | **200 draw calls**; re-mems on hover |
| `GenreLabels` → `GenreLabel` | L400-471 | 1 Troika `<Text>` per labeled genre (~50-80) | NO | each text owns SDF atlas | **YES, one `useFrame` per label** (50+ hooks) | **MAJOR — 50+ useFrames just to adjust `fillOpacity`**; runs r3f dispatch 50x/frame |
| `AmbientDust` | L521-633 | 1 `<points>` (800 pts) | — | memoized | yes, **throttled 30Hz** (`rpFrameSkip%2`) | already optimized |
| `SceneConnections` | L637-706 | **1 `<line>` per pair** up to ~N²/2 in same scene → could easily hit 300+ | NO | re-mems on year | no | **300+ draw calls** for ambient web |
| `ActiveGenreGlow` | L709-732 | 1 pointLight | — | — | yes (60 Hz) | dynamic light forces shader recompile on Standard mats |
| `ClusterLights` | L735-769 | up to ~12 pointLights (static) | — | — | no | **light count pushes Standard material to N-light branch**; each extra dynamic light = +fragment cost on every StdMat draw |
| `BiomeLabels` | L772-824 | 1 `<Html>` per scene (~12) | — | — | no | DOM |
| `DecadeLabels` | L829-872 | 1 `<Html>` per decade (~6) | — | — | no | DOM |
| `CameraIdleBob` | L875-903 | 0 | — | — | yes (60 Hz) | cheap |
| `MysteryNode` | MN.jsx | 1 mesh + 1 glow | NO | inline `<sphereGeometry args=[1,24,24]>` re-created each render | yes (60 Hz) | two spheres, inline geo |
| `LabelConstellation` | LC.jsx | up to 30 `<line>` + 30 `<mesh ringGeometry>` | NO | per-instance `BufferGeometry` via useMemo | yes, **one useFrame per GlowMarker** | 30 extra useFrames |
| `ArtistThread` | AT.jsx | 1 CatmullRom line + N `<ReleaseMarker>` | NO | per-comp | yes, **one useFrame per marker + 1 for line** | N+1 useFrames |
| `DigPath` | DP.jsx | 1 line + N waypoint groups | NO | per-comp | yes | only active in record mode |

**Tally for typical genre view:** ~**8-12 instanced draw calls** (cheap) + **~500 individual line draw calls** (links + scene connections) + **~80 Troika Text draw calls** + `useFrame` registered on **~80-100 distinct components** (each label, each marker, each glow).

### 1.2 `GenrePlanet.jsx` (1026 lines, vanilla Three, no R3F)

- **Planet mesh:** `SphereGeometry(100, 128, 128)` = 128² = **16,384 segments** → ~33k vertices, fully displaced in JS. Build cost ~50-150 ms, runs once.
  - `buildPlanetMesh` does O(vertices × territories) = 33k × ~150 = ~5M acos calls on load. One-shot but blocks main thread.
- **Ocean mesh:** SphereGeometry(99.5, 96, 96) = ~18k verts, **vertex shader runs simplex noise per frame per vertex** (`snoise` in vertex shader × 3 octaves). Expensive but GPU-side.
- **Nebula:** Sphere(900, 32, 32) with **4-octave value noise per fragment**. Full-screen-ish fragment shader — real cost. L429-490.
- **City lights:** Points w/ custom shader, cheap.
- **Territory borders:** Points w/ 12 segments × N² pairs up to ~400 territories → can be 1000s of points. Cheap (1 draw call).
- **Atmosphere:** 3 extra spheres (Fresnel, outer, inner glow) + `requestAnimationFrame` loop that **fights the main animate loop** (L87-92 of GlobeAtmosphere.js — independent rAF rotating meshes, never cancelled on re-render).
- **Starfield:** InstancedMesh 2000 stars.
- **Bloom:** UnrealBloomPass at half-res (`GlobeBloom.js` L35).
- **Building LOD:** `buildingSystem.js` — `getSurfacePoint` at L35-58 does **linear scan over all 33k planet verts** each time a building is placed (`for (i=0; i<count; i+=3)`). Called for **every building × every territory visited**. Cost: ~60 buildings × 11k iters = 660k iterations per territory open. Not per-frame but blocks on click.
- **Hover raycast:** L815 throttled to ~3 frames (20 Hz) ✓ already done.
- **Entire render loop is in plain rAF**, NOT R3F's scheduler — so `AdaptiveDpr` / `AdaptiveEvents` / `frameloop='demand'` don't apply. Planet view cannot benefit from drei helpers.

### 1.3 `EarthGlobe.jsx`

- globe.gl owns its own scene graph + Three renderer. Atmosphere + Starfield + Bloom composer added on top. Textures loaded from unpkg CDN at runtime (**no prefetch / preload tag**).
- **Shops layer** toggled every 200 ms via `setInterval` checking `pov.altitude` (L309-323) — switches `globe.pointsData()` which triggers three-globe geometry rebuild. Threshold debounce is fine; `setInterval` at 200 ms creates GC noise.
- Bloom composer double-renders (globe.gl internal + our composer) after `renderer.setAnimationLoop(null)` is called at L338 — one pipeline wins. Good.
- **No LOD on cities, shops, arcs** — all HTML markers (1500+ cities) kept in DOM when `htmlElementsData(cities)` is set.

### 1.4 `ReleaseParticles.jsx`, `Stars.jsx`, `GlobeBloom.js`, `GlobeAtmosphere.js`, `GlobeStarfield.js`

- `ReleaseParticles`: up to `data.particles.length` points, throttled 30 Hz ✓.
- `Stars`: 3000 pts on desktop, 500 mobile. Single useFrame rotates + modulates opacity. Fine.
- `GlobeAtmosphere`: 3 sphere shells (64/48/48 segments) + **independent rAF loop at L87 that is NOT cancelled in cleanup** (see cleanup L94: cancels `animId` ✓ — OK actually, I misread initially). But it IS a separate rAF running regardless of paused state → runs when tab is backgrounded unless browser throttles.
- `GlobeBloom`: half-res UnrealBloom, strength 1.2 radius 0.4 threshold 0.8. Desktop-only use (App.jsx L180 `{!isMobile && <AudioReactiveBloom/>}`) but EarthGlobe + GenrePlanet add it for BOTH mobile and desktop (GlobeBloom called unconditionally in EarthGlobe L330).
- `GlobeStarfield`: 2000 InstancedMesh of tiny spheres with `SphereGeometry(0.3, 4, 4)` = 12 tris each = 24k tris total. Could be 1 Points draw call instead.

### 1.5 Drei usage (checked)

- `<AdaptiveDpr pixelated />` — present in `App.jsx` L182 ✓
- `<AdaptiveEvents />` — **NOT used**
- `<BakeShadows />` — **NOT used** (no shadow maps so N/A, but `receiveShadow` set on Ground at GenreWorld L32 without any light casting shadows → dead property, no-op)
- `<PerformanceMonitor />` — **NOT used** (would enable auto-quality downgrade)
- `<Instances>` / `<Merged>` (drei instancing helpers) — not used; vanilla `<instancedMesh>` instead (fine)

### 1.6 GPU/shader budget

- **Postprocessing chunk 397 KB** (`postfx-CEtsvX-U.js`) loaded on desktop only for `<Bloom />` — plus GenrePlanet and EarthGlobe each have their own `three/examples/jsm/postprocessing/UnrealBloomPass` import via `GlobeBloom.js`, which is in the `three` chunk. So desktop users pay for **two bloom implementations**: pmndrs postprocessing (genre view) + three-examples UnrealBloomPass (earth + planet). Different code paths, same visual goal.
- On `genre` view: only `<Bloom>` (mipmapBlur:false, desktop only). Light.
- On `earth`/`planet`: UnrealBloom + extra fresnel shader + ocean wave shader + nebula shader. Heaviest.

---

## 2 — R3F / Three.js best practices checked against code

Research baseline (r3f v9, three r180+ assumed; DiscoWorld is on three r180 per `three-RnHnqt0E.js` chunk size).

| Pattern | Applied? | Location |
|---|---|---|
| `InstancedMesh` for repeated geometry | PARTIAL — genre spheres, wireframes, buildings, stars use it. **Links/connections do NOT.** | GenreWorld L354, L221 vs L506, L686 |
| Geometry/material via `useMemo` | PARTIAL — module-level consts good; **`<ringGeometry>` in GlowRings L95 and `<sphereGeometry>` in MysteryNode L105/118 are inline JSX → new geo every render** | GenreWorld L95, MN L105, L118 |
| `frameloop="demand"` when idle | NO — always `frameloop="always"` on genre canvas | App.jsx L454 |
| `<PerformanceMonitor>` → auto DPR | NO | — |
| `<AdaptiveEvents />` | NO | — |
| `BatchedMesh` (Three r160+, single draw call for mixed geometries) | NO | — |
| `three-mesh-bvh` for raycast | bundled (in `three` chunk per vite.config L132) but **NOT used** — planet raycast uses naive `intersectObject` | GenrePlanet L649, L817 |
| GPU picking (color-id framebuffer) | NO — relies on raycaster | — |
| `frustumCulled` defaults | default `true` except buildingSystem.js L121 explicitly disables it (OK, tiny objects) |
| Merged/batched line segments for `<GenreLinks>` / `<SceneConnections>` | NO — 500+ individual `<line>` components | GenreWorld L506, L686 |
| Troika text atlas sharing | Troika auto-shares SDF atlas per font. But **50+ `<Text>` = 50 draw calls** (each is a separate mesh). Solution: `<Text>` batching via `<Instances>` is impossible for Troika; alternative is fewer labels or HTML labels with CSS 3D transforms. |
| Fog / frustum culling | fog set in App L148, frustum culling on by default for non-instanced, disabled implicitly on instanced (Three enables it on the parent instanced mesh only — if bounding sphere is wrong, nothing culls) |

---

## 3 — Concrete bugs / anti-patterns found

### BUG 1 — Inline geometry re-creation (`GlowRings`, `MysteryNode`)
- `GenreWorld.jsx:95` — `<ringGeometry args={[r.radius * 0.85, r.radius, 64]} />` inside `.map()` inside render. **Every parent re-render (year change, audio tick, anything) re-allocates 12 ring geometries** = 12 × 64 segments × 3 floats. Should be `useMemo(() => new THREE.RingGeometry(...), [radius])` once per ring.
- `MysteryNode.jsx:105` — `<sphereGeometry args={[1, 24, 24]} />` inline → 577 verts re-allocated every render of MysteryNode (component re-renders on hover: L26 `hovered` state).

### BUG 2 — 50+ useFrame subscribers in `GenreLabels`
- Each `<GenreLabel>` L432 registers its own `useFrame` at L440 just to update `fillOpacity`. With ~80 labels: **80 r3f dispatches per frame** for a trivial distance check. Should be one shared `useFrame` at `GenreLabels` level iterating ref array.

### BUG 3 — Hundreds of individual `<line>` draw calls
- `GenreLinks` (up to ~200 lines, GenreWorld L506) and `SceneConnections` (up to ~300 lines, L686) each emit **one `<line>` mesh per link**. These should be merged into a single `THREE.LineSegments` with a BufferGeometry holding all segment endpoints (or `Line2` from examples for thickness).
- Current: ~500 draw calls from lines alone. Target: 2.

### BUG 4 — `meshStandardMaterial` on all 166 genre spheres + 3000 buildings + planet, with 4+ dynamic lights in Scene
- 4 dynamic lights (ambient + 2 pointLights + 1 dirLight) × every StandardMaterial fragment = real cost, especially on integrated GPUs. `ActiveGenreGlow` adds a 5th. `ClusterLights` adds up to 12 more.
- **Suggestion:** downgrade non-hero meshes (buildings, wireframes) to `MeshLambertMaterial` or `MeshBasicMaterial` with vertex colors. Buildings especially don't need PBR.

### BUG 5 — `WaypointMarkers`, `GlowMarker`, `ReleaseMarker` — one useFrame per item
- Same anti-pattern as BUG 2: LabelConstellation, ArtistThread, DigPath each spawn N individual components with N useFrames. Should be hoisted to parent loop with shared ref array.

### BUG 6 — `getSurfacePoint` O(vertices) linear scan per building placement
- `buildingSystem.js:44` walks 33k vertices to find nearest to a direction. Runs ~60 times per territory click. ~2 M iterations per click. Should be replaced with spatial lookup (kd-tree, or better: just compute displaced point analytically since the territory center is known).

### BUG 7 — EarthGlobe `setInterval(..., 200)` poll for altitude
- `EarthGlobe.jsx:309` — 5 Hz poll for `pov.altitude` to toggle shops visibility. Creates allocation pressure. Use `controls.addEventListener('change', ...)` or throttle via rAF.

### BUG 8 — `frameloop='never'` on hidden Canvas doesn't release GPU
- `App.jsx:454` — `frameloop={viewMode === 'genre' ? 'always' : 'never'}`. Good, but the Canvas is kept with `display:none` (L441) and its WebGL context stays alive. Switching views twice = ≥2 WebGL contexts (genre + earth or planet) simultaneously. Safari caps at 16 contexts; heavy desktop drivers stutter at 2-3. Needs explicit dispose or `key` remount.

### BUG 9 — `SceneConnections` and `GenreLinks` memoize on `hoveredSlug`
- GenreLinks L501 depends on `hoveredSlug` in its `useMemo`, meaning **every hover hover-out event rebuilds 200 BufferGeometries** just to change a color. Separate the color (per-line material uniform or instance attribute) from the geometry.

### BUG 10 — `ClusterLights` + StandardMaterial cost multiplication
- Up to 12 point lights in the scene at once. Three.js recompiles shader programs based on light count; more importantly each frag runs `#pragma unroll_loop` over 12 lights even for far-away pixels. Real cost on mobile GPUs. Replace most cluster lights with emissive + bloom.

---

## 4 — Recommended optimizations (prioritized backlog)

Expected FPS gains assume Apple M1-class integrated GPU at 1440p, 166 genres, genre view. Rough estimates from pmndrs benchmarks + three.js forum reference cases. Effort in engineer-hours.

| # | Fix | Est FPS gain | Effort | Anchor |
|---|---|---|---|---|
| 1 | **Merge `GenreLinks` + `SceneConnections` into 2 `THREE.LineSegments` with single BufferGeometry** — drops ~500 draw calls to 2. Color via per-vertex attribute, not per-line material. | +12-20 FPS | M (3-4 h) | `GenreWorld.jsx:506`, `:686` |
| 2 | **Hoist per-label `useFrame` → single loop at `GenreLabels` parent** iterating `textRefs.current`. Kills 80 r3f dispatches/frame. Apply same pattern to `LabelConstellation.GlowMarker`, `ArtistThread.ReleaseMarker`, `DigPath.WaypointMarkers` (already batched, keep). | +3-6 FPS | S (1-2 h) | `GenreWorld.jsx:440`, `LabelConstellation.jsx:37`, `ArtistThread.jsx:68` |
| 3 | **Replace `ClusterLights` + `ActiveGenreGlow` point lights with emissive materials + single keep-bloom**. Reduces fragment shader branches on every StandardMat draw. Cut dynamic lights from 6-17 → 3 max. | +5-10 FPS | M (2 h) | `GenreWorld.jsx:735`, `:709` |
| 4 | **Downgrade buildings from `meshStandardMaterial` to `meshLambertMaterial`** (or MeshBasic with a faux-gradient). 3000 instances × cheaper shader = big win on mobile/integrated. | +4-8 FPS | XS (15 min) | `GenreWorldBuildings.jsx:91,109,127` |
| 5 | **Fix inline geometry allocations**: memoize `<ringGeometry>` in `GlowRings` and extract `<sphereGeometry>` in `MysteryNode` to module-level consts. Removes GC pressure + re-uploads. | +1-3 FPS + smoother (no GC hitches) | XS (30 min) | `GenreWorld.jsx:95`, `MysteryNode.jsx:105,118` |
| 6 | **Add `<PerformanceMonitor>` from drei** → auto-downgrade DPR / disable bloom when FPS <45. One wrapper around `<Scene>`. Immediate win on any device below M1. | +0 FPS on fast hw, **+15-30 FPS** on slow | S (1 h) | `App.jsx:141` (Scene) |
| 7 | **Memoize GenreLinks on `[genres, links, year]` only**, move active/hover highlight to material uniform. Stops 200 BufferGeometry rebuilds per hover tick. | +2-4 FPS during hover | S (1-2 h) | `GenreWorld.jsx:501` |
| 8 | **Replace `getSurfacePoint` linear 33k-vertex scan with analytical projection** (use territory dir × displaced-radius from biome height formula). Eliminates click-lag (~100 ms) when opening territories on Planet. | No FPS change, but removes stutter | S (1-2 h) | `buildingSystem.js:44` |
| 9 | **`<AdaptiveEvents />` in Canvas** + switch genre Canvas to `frameloop='demand'` with `invalidate()` on audio ticks / hover / camera move. Goes from continuous 60 Hz → 0 Hz when idle. Massive laptop battery win. | +0 active, saves 70% GPU idle | M (2-3 h) | `App.jsx:454` |
| 10 | **Kill globe.gl Starfield InstancedMesh (2000 × 24-tri spheres) and replace with `THREE.Points`** (single draw call). Already have `Stars.jsx` doing exactly this for genre view. | +2-4 FPS on earth/planet | XS (20 min) | `GlobeStarfield.js:13` |
| 11 | **Dispose Canvas/globe WebGL context on view switch** (use `key` prop to remount or explicit `gl.dispose()`). Prevents 2-3 live contexts simultaneously. | +3-5 FPS after view switches; prevents Safari crash | M (2 h) | `App.jsx:441` |
| 12 | **Planet ocean shader: octaves 3 → 1** (or precompute normal map). Vertex-shader noise on 18k verts per frame is the single biggest GPU cost on Planet view. | +8-15 FPS on planet | S (30 min) | `GenrePlanet.jsx:304-306` |

---

## 5 — Prioritized backlog (ROI = Impact ÷ Effort)

| Priority | Fix | FPS impact | Effort | Anchor |
|---|---|---|---|---|
| **P0** | Merge 500+ `<line>` meshes into 2 LineSegments | **+12-20 FPS** | M (3-4 h) | `GenreWorld.jsx:506,686` |
| **P0** | `<PerformanceMonitor>` auto-DPR/bloom gate | **+15-30 FPS on weak GPUs** | S (1 h) | `App.jsx:141` |
| **P0** | Drop buildings to `MeshLambertMaterial` | +4-8 FPS | XS (15 min) | `GenreWorldBuildings.jsx:91,109,127` |
| **P1** | Hoist 80+ `useFrame` → single loop for labels + markers | +3-6 FPS | S (1-2 h) | `GenreWorld.jsx:440`, `LabelConstellation.jsx:37`, `ArtistThread.jsx:68` |
| **P1** | Ocean shader octaves 3 → 1 (planet view) | +8-15 FPS (planet) | S (30 min) | `GenrePlanet.jsx:304-306` |
| **P1** | Reduce cluster/glow point lights → emissive | +5-10 FPS | M (2 h) | `GenreWorld.jsx:735,709` |
| **P2** | Memoize inline geometries (rings, MysteryNode spheres) | +1-3 FPS + smoother | XS (30 min) | `GenreWorld.jsx:95`, `MysteryNode.jsx:105,118` |
| **P2** | GenreLinks: color via uniform, not geometry rebuild | +2-4 FPS on hover | S (1-2 h) | `GenreWorld.jsx:501` |
| **P2** | `frameloop='demand'` + `<AdaptiveEvents>` | idle GPU -70% | M (2-3 h) | `App.jsx:454` |
| **P2** | Dispose WebGL context on view switch | +3-5 FPS post-switch, crash-safety | M (2 h) | `App.jsx:441` |
| **P3** | `buildingSystem.getSurfacePoint` analytical | removes 100 ms click stutter (planet) | S (1-2 h) | `buildingSystem.js:44` |
| **P3** | GlobeStarfield → `THREE.Points` | +2-4 FPS (earth/planet) | XS (20 min) | `GlobeStarfield.js:13` |

**Total expected desktop gain (P0+P1):** **+30-60 FPS headroom** on integrated GPUs (where current state likely hovers 30-45 FPS). On M1 Pro+ where 60 is already capped, wins become battery life (fan silent instead of ramping).

**Total expected mobile gain:** biggest wins are P0 (#1 merge lines, #2 PerformanceMonitor) — likely takes DiscoWorld from ~20-25 FPS to smooth 45-60 FPS on mid-tier Android.

---

## 6 — Not a fix but worth flagging

- `vite.config.js` manualChunks logic is already tight. `postfx` chunk (397 KB) is the big ticket; it's desktop-gated at runtime but still downloaded preemptively because `@react-three/postprocessing` is statically imported in `App.jsx:5`. **Dynamic import it** only when `!isMobile`:
  ```js
  const AudioReactiveBloom = lazy(() => import('./components/AudioReactiveBloom'))
  ```
  Saves 397 KB gzip on mobile first-paint.
- `globe` chunk is 1.8 MB, only loaded on `earth` view — already lazy. Good.
- three chunk 309 KB includes `three-mesh-bvh` that is never used — tree-shake candidate.
- `BakeShadows` / `receiveShadow` on Ground (GenreWorld L32) is misleading — no shadow casters, no shadow maps enabled on renderer. Remove the prop.
- GenreWorld file is 997 lines with 16 internal components — splitting into `GenreWorld/*.jsx` would make future perf audits tractable.

---

*Audit complete. Next action: apply P0 fixes in a worktree, benchmark with `<PerformanceMonitor>`-reported FPS before/after.*
