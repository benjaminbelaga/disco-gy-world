# Agent B — DiscoWorld Label Readability Audit

**Date:** 2026-04-17
**Scope:** make the ~166 genre labels in `GenreWorld.jsx` read like a treasure-map of continents and islands instead of a noisy floating cloud of text.
**Data measured (from `public/data/world.json`):**

- 166 genres, 28 "scenes" (biomes)
- `trackCount`: max 256, median 58, only 36 genres >= 100
- Longest label: "Oldskool Rave Hardcore" (22 chars)
- Scenes range 2-12 genres. 22 of 28 have >= 3 members (viable centroids)

---

## 1. Current label surface (as-is)

All label rendering lives in `packages/web/src/components/GenreWorld.jsx`. Three distinct systems, mixed primitives:

| Layer | Primitive | Count | File anchor | Issue |
|---|---|---|---|---|
| Genre name | drei `<Text>` (SDF via troika) | 36 of 166 (tracks >= 100) | `GenreWorld.jsx:432-471` (`GenreLabel`) | tiny fontSize (1.0-2.4 world units), hard-coded `depthOffset=-1` with no `renderOrder`, no billboarding, opacity math is a two-branch ternary with magic numbers, no LOD collapse at distance |
| Scene/biome name | drei `<Html>` (DOM) | 28 | `GenreWorld.jsx:772-824` (`BiomeLabels`) | `fontSize:16px` in CSS, letter-spacing 4px, good — BUT 28 HTML nodes all always on with no occlusion, no distance fade, stack above subgenre `<Text>` because Html is on top of the WebGL layer with no z-control |
| Decade | drei `<Html>` (DOM) | up to 7 | `GenreWorld.jsx:829-872` (`DecadeLabels`) | rgba(240,235,224,0.22) — essentially invisible; 28px; no occlusion |
| Hover tooltip | drei `<Html>` | 1 | `GenreWorld.jsx:376-397` | OK |
| Custom glow marker, constellation overlay | none | — | `LabelConstellation.jsx` | no text, uses colored spheres |

**Counts of `<Text>` / `<Html>` instances in the 3D scene at steady state:** up to **36 SDF Text meshes + 28+7+1 = 36 DOM Html nodes = 72 label-bearing nodes**, all rendered every frame regardless of camera distance, occlusion, or overlap.

**Concrete bugs spotted:**

1. `GenreLabel` (line 432) never billboards — the text is authored on the XZ plane and `anchorY="bottom"` orients it, but from a low angle the text is almost edge-on. Drei's `<Text>` is not billboarded by default.
2. `GenreLabel` sets `depthOffset={-1}` but the troika material still writes to depth, so near-distance labels z-fight with the genre spheres (spheres float up-down via `Math.sin(t*0.5 + g.x*0.1)*0.3`, labels do not follow the float, so their Y drifts out of the sphere and the `outlineWidth=0.12` runs into adjacent wireframes).
3. `GenreLabels` filters `trackCount >= 100` → 36 labels. In low-track scenes (Electro: 2 genres, trackCount 43/78; Ambient: 3, top=96) **zero** labels show at all. Whole regions read as empty.
4. `BiomeLabels` renders **all 28** `<Html>` simultaneously with no culling — on mobile, 28 DOM nodes with `text-shadow: 0 0 16px currentColor, 0 2px 6px rgba(...)` is an expensive paint. drei docs note Html overhead scales poorly; even 2,500 Html was reported unusable, 28 is fine for perf but they all overlap and flicker as the user pans because DOM nodes can't z-sort against the 36 SDF labels.
5. `DecadeLabels` uses `color: 'rgba(240,235,224,0.22)'` — 22% alpha on a near-black background at 28px. Essentially invisible on laptop screens (I would bet Ben never saw them fire).
6. `GenreLabel` fontSize formula `1.0 + sqrt(g.trackCount / 256) * 1.4`. Floor is 1.0 world unit, ceiling 2.4. Camera sits ~50-110 units away (the fade math at line 448-449 confirms this). At 60 units a 1.0-unit letter occupies ≈16 pixels of a 900px viewport — legible, but the outline at 0.12 units is 12% of the letter height, making letters appear bold+bloated.
7. Genre name font is drei `<Text>`'s **default Roboto** — the app loaded Space Grotesk and JetBrains Mono globally (`index.css:1`), but `<Text>` fetches its own `.woff` at runtime. Two visual tracks = no brand coherence.
8. `BiomeLabels` onClick handler does `setActiveGenre(b.primary) + setCameraTarget(b.primary)` where `primary` is the highest-trackCount genre — so clicking "House" jumps to the single biggest house subgenre, not the centroid. Confusing.
9. No collision detection between labels. At a Trance cluster of 6 labels within ~10 units, text runs over text.
10. No responsive typography — same world-unit fontSize on iPhone 375px as on 27" retina.

---

## 2. `<Text>` vs `<Html>` trade-offs (verified via drei docs and perf discussions)

| Dimension | drei `<Text>` (troika SDF) | drei `<Html>` (DOM portal) |
|---|---|---|
| Renderer | WebGL mesh w/ SDF atlas | DOM element positioned via `calculatePosition` each frame |
| DPI | Sharp at all zooms, SDF auto-scales | Sharp on retina, subpixel AA, picks up browser font smoothing |
| Cost at N=30-100 | cheap — instanced atlas, one drawcall per font | ≈1-2ms per frame per node for `updateWorldMatrix` + DOM write |
| Cost at N=1000+ | still cheap (<5ms) | unusable (reports of >100ms, scene judder) |
| Z-sorting with scene | native — writes to depth buffer, occluded by geometry | separate stacking context, bolted on top of canvas unless `occlude` ref given |
| Outline / halo | native `outlineWidth`/`outlineColor`/`outlineBlur` (SDF) | CSS `text-shadow`, blur expensive |
| Transparency | works; set `fillOpacity`, keep `depthWrite` off | free |
| Billboard | needs wrapping `<Billboard>` or custom matrix | automatic (always camera-facing) |
| Anti-aliasing | near-perfect (SDF) at every scale | browser native |
| Layout | one-line + `maxWidth` + `textAlign` — no flex | full CSS |
| Event handling | pointer events via 3D raycast | native DOM events |

**Verdict for DiscoWorld's 166-genre scene:** SDF `<Text>` for every label that lives "in the world" (genres + biome continent names), `<Html>` reserved for UI that needs CSS layout (tooltip, side panels). Keep total `<Text>` instance count under ~200 to stay cheap.

---

## 3. LOD strategies for 3D labels (survey)

Proven patterns from data-viz / cartography / games:

1. **Distance-based fade + cull** — linear fade between near/far thresholds, hard cull beyond. Already half-implemented in `GenreLabel:442` but with magic-number opacity math; formalize as tokens.
2. **Tier-based "unfurl"** — primary (biome/continent) labels ALWAYS visible, secondary (top 10-20% genres by trackCount) visible mid-range, tertiary (rest) only at close zoom. Mirrors Mapbox/MapLibre `minzoom`/`maxzoom` per feature.
3. **Density clustering** — when camera is far, collapse same-scene labels into ONE continent label at the scene centroid; when camera approaches, fade continent OUT and fade individual genre labels IN. This is the "zig-zag.fm continent" feel Ben asked for.
4. **Screen-space collision** — project each label's AABB to NDC, sort by priority (trackCount), drop any that overlap a higher-priority box. drei has no built-in, but a `useFrame` pass over ~50 labels is sub-millisecond. Simpler proxy: angular separation test (dot product of direction-from-camera) + min-pixel-gap.
5. **Salience budget** — cap total visible labels by tier (e.g., 1 scene label always + 12 primary genre labels + 24 secondary at close zoom). Prevents noise explosion when panning over dense biomes.
6. **Drei `<Detailed>`** — built-in LOD wrapper that swaps children by distance. Useful for per-label "full text → initials → nothing" ladder, but overkill when a single shader uniform can do fade.
7. **Pool + virtualize** — mount a fixed pool of ~50 `<Text>` instances, recycle them across the closest N genres. Only needed beyond ~200 labels. DiscoWorld doesn't need this yet.

**DiscoWorld fit:** combine (1)+(2)+(3)+(4). Skip (6) (over-engineered) and (7) (not needed at N=166).

---

## 4. Text halos / outlines / contrast in 3D

- **drei `<Text>` native:** `outlineWidth` (world units OR "10%" string relative to font size), `outlineColor`, `outlineOpacity`, `outlineBlur` (soft halo), `strokeWidth`/`strokeColor`/`strokeOpacity` for inner stroke. These are SDF-derived — free to render, crisp at every zoom. Recommended recipe for legibility on a dark nebula: `outlineWidth="8%" outlineColor="#050510" outlineBlur="15%"` — soft dark halo that kills the black-on-dark vanishing problem without looking like a fake drop-shadow.
- **Dual-pass halo trick:** render the same text twice — big blurry version behind (outlineBlur="40%") + sharp one in front. drei doesn't have this as a prop; wrap two `<Text>` in one group. Produces the "cinematic credit roll" glow.
- **Billboard + background pill:** for biome labels wrap `<Text>` in a `<mesh>` with a tiny rounded plane behind it (e.g., a 9-slice frame), tinted by `genre.color` at 15% alpha. Reads like a treasure-map cartouche.
- **CSS text-shadow on `<Html>`:** what the current code does for BiomeLabels — works but can't occlude behind mountains/planets. Use only when the label must sit above WebGL always.

---

## 5. Typography for data-viz / 3D (what to standardize)

Cartography rules that transfer well:

- **Pair 1 display + 1 mono.** Space Grotesk (already loaded) for proper nouns (biome names, genre names). JetBrains Mono for meta (decade, count, BPM, year). Don't mix weights within a tier.
- **Uppercase + letter-spacing for areas** (continents/biomes): 4-6px tracking, 600-700 weight. Current `BiomeLabels` already does this — keep it, promote to SDF.
- **Mixed case for points** (genres): sentence case, 500 weight, tracking 0, to contrast with the areas.
- **Dynamic type scale by tier:**
  - T0 biome/continent: 2.2 world units, uppercase, tracked
  - T1 primary genre (trackCount top-quartile, >= 120 tracks here): 1.6 world units, sentence case
  - T2 secondary genre (40-120): 1.1 world units, sentence case, 70% opacity
  - T3 tertiary (< 40): 0.8 world units, only on close zoom
  - T4 decade: 3.0 world units, mono, 35% opacity (promoted from current invisible 22%)
- **Character set sanity:** drei Text with a woff font of Space Grotesk — confirm it covers `&`, `/`, `’`. Genre names contain "n" (as in "Drum n Bass"). Pre-render the full Latin-1 subset in the font file.
- **Minimum pixel size rule:** target min 11px on screen. Compute per-frame: `pixelSize = fontSize * viewportHeight / (2 * dist * tan(fovY/2))`. If pixelSize < 11, cull.

---

## 6. Proposed label system (concrete spec)

### Data model additions (compute once in the store)

```js
// useStore.js — enrich genres at load time, run ONCE
const enrich = (genres) => {
  const sorted = [...genres].sort((a,b) => b.trackCount - a.trackCount)
  const p25 = sorted[Math.floor(sorted.length * 0.25)].trackCount // ≈ 120 in current data
  const p60 = sorted[Math.floor(sorted.length * 0.60)].trackCount // ≈ 40
  return genres.map(g => ({
    ...g,
    tier: g.trackCount >= p25 ? 1 : g.trackCount >= p60 ? 2 : 3,
  }))
}
```

Biome centroids computed in a `useMemo` with a secondary `representative` = the highest-tier genre closest to the centroid (not just max-trackCount). This fixes bug #8.

### Render strategy

All label rendering moves to SDF `<Text>` (no more `<Html>` for in-world labels). Wrap each in `<Billboard lockY>` so the text always faces the camera but stays upright (no roll). One shared material, one shared font file — drei Text will batch when the font prop is the same.

Tiered component split:

```jsx
<ContinentLabels genres={genres} />   // T0 — 28 biome names, always visible
<PrimaryGenreLabels genres={genres} /> // T1 — ~42 labels, visible always
<SecondaryGenreLabels genres={genres} /> // T2 — ~58 labels, fade 60->90u
<TertiaryGenreLabels genres={genres} /> // T3 — ~66 labels, fade 30->55u only
<DecadeOverlay genres={genres} />     // T4 — 3D SDF ghosted decade text
```

`<ContinentLabels>` replaces current `BiomeLabels` — SDF text at scene centroid, 2.2 units, uppercase, `outlineWidth="8%"`, `outlineColor="#05070e"`, `outlineBlur="25%"`, color derived from scene's dominant color at 90% saturation. Fades OUT as camera approaches (distance 0-30 units → opacity 0, 30-60 → lerp up to 0.9). So: far = continents; close = genres.

### LOD curve (per tier)

```
tier 0 (continent): dist 0-30  opacity lerp 0 → 0.9
                    dist 30-∞  opacity 0.9
                    inverted pattern: biomes fade as you zoom in
tier 1 (primary) :  dist 0-120 opacity 1
                    dist 120-150 fade to 0
tier 2 (secondary): dist 0-60  opacity 1
                    dist 60-90 fade to 0
tier 3 (tertiary):  dist 0-25  opacity 1
                    dist 25-40 fade to 0
                    (camera default is ~50 so these only appear on zoom-in)
tier 4 (decade):    always 0.35 opacity, always visible
```

### Collision pass (cheap)

Every frame, in one `useFrame` shared across label layers:

1. Project each tier 1+2 label centre to NDC.
2. Sort by `(tier ASC, trackCount DESC)`.
3. Walk list; skip label if its NDC bbox intersects any already-kept bbox within a 12px pad.
4. Set `.visible = kept` on each ref.

Budget: 166 matmul + 166 bbox tests = <0.3ms.

### Typography tokens (share with Agent C)

```js
// tokens/labels.js
export const LABEL_TOKENS = {
  font: '/fonts/SpaceGrotesk-Medium.woff',           // place in public/fonts
  fontBold: '/fonts/SpaceGrotesk-SemiBold.woff',
  tiers: {
    0: { size: 2.2, weight: 'bold', tracking: 0.22, case: 'upper', color: 'biome' },
    1: { size: 1.6, weight: 'medium', tracking: 0,    case: 'sentence', color: 'genre' },
    2: { size: 1.1, weight: 'medium', tracking: 0,    case: 'sentence', color: 'genre-muted' },
    3: { size: 0.85, weight: 'medium', tracking: 0,   case: 'sentence', color: 'genre-muted' },
    4: { size: 3.0, weight: 'medium', tracking: 0.3,  case: 'upper', color: '#8892a6', alpha: 0.35 },
  },
  outline: { width: '8%', color: '#05070e', opacity: 1, blur: '15%' },
  minPixelSize: 11,
}
```

---

## 7. Concrete code-level changes (5-8 edits, ready to hand to Agent E)

1. **`GenreWorld.jsx:400-430` — rewrite `GenreLabels`** to split into `<PrimaryGenreLabels>`, `<SecondaryGenreLabels>`, `<TertiaryGenreLabels>`; remove the `trackCount >= 100` hard filter; consume `g.tier` from the store. Wrap each `<Text>` in `<Billboard follow lockX lockZ>` from drei.
2. **`GenreWorld.jsx:432-471` — rewrite `GenreLabel`** to take `tier` prop, pull size/weight/case from `LABEL_TOKENS.tiers[tier]`, pass `font={LABEL_TOKENS.font}`, `outlineWidth="8%"`, `outlineColor="#05070e"`, `outlineBlur="15%"`, `fillOpacity` driven by a single shared LOD function `labelOpacityForTier(tier, dist)`, add `material-toneMapped={false}` so the outline reads on bloomed scenes, set `renderOrder={1000 + tier}` (and `material-depthTest={false}` for tier 0 only, so continent names never hide behind terrain).
3. **`GenreWorld.jsx:772-824` — replace `BiomeLabels` `<Html>` with SDF `<Text>`** using tier 0 tokens, wrap in `<Billboard lockY>`, compute inverse-distance opacity so continents fade out as user zooms in. Move the onClick to a transparent hit-plane behind the text (or use drei's `interactive` prop on the group) — cleaner than binding click on the DOM node. Fix "primary" centroid bug: pick genre closest to centroid, not max-trackCount (line 786).
4. **`GenreWorld.jsx:829-872` — replace `DecadeLabels` `<Html>` with `<Text>`** at fontSize 3.0, opacity 0.35, color `#8892a6`, `outlineColor="#0a0a14" outlineOpacity={0.6}`, position `y=6` (not 8, too high), `rotation={[-Math.PI/2, 0, 0]}` so the decade name lies flat on the ground plane like a map cartouche. Kills the invisible 22%-alpha bug and the second DOM layer.
5. **`GenreWorld.jsx` (new, ~line 398) — add `LabelCollisionManager`** — one `useFrame` component that walks refs from tier 1/2/3 labels, does NDC bbox collision, writes `.visible` on each label `textRef`. Register each `<Text>` ref via a context or a `useLabelRegister()` hook that pushes `{ ref, tier, trackCount, position }` into a shared array.
6. **`stores/useStore.js:142-145` — enrich genres** on `setGenres`: compute `tier`, compute per-scene centroid, compute `representative` genre per scene (closest to centroid, tier <= 1 preferred). Store derived maps `scenesById`, `genresByTier` to avoid recomputing every render.
7. **`packages/web/public/fonts/` — ship Space Grotesk woff files** and wire `<Text font="/fonts/SpaceGrotesk-Medium.woff">` so the label font matches the app's UI font (fix bug #7, dual typography track). Preload with `<Preload all />` already in `App.jsx:4`.
8. **`packages/web/src/components/GenreWorld.jsx:14` (shared `_sphere` section)** — add `import { Billboard } from '@react-three/drei'` and a single shared `<LabelGroup>` wrapper that applies `renderOrder={1000}`, `frustumCulled={false}` on the root group (labels must render even when their anchor mesh is culled), and `raycast={() => null}` on tertiary tier labels so they never steal pointer events from the genre spheres.

### Bonus (if time): LOD debug HUD

Press `L` → toggle HUD showing "T0 visible: 22 / T1: 38 / T2: 14 / T3: 0 / collisions dropped: 7 / avg px size: 14". Makes the LOD curve tunable in-session without rebuilding.

---

## Sources

- [drei Text / SDF documentation](https://github.com/pmndrs/drei/blob/master/docs/abstractions/text.mdx)
- [drei Html component props](https://github.com/pmndrs/drei/blob/master/docs/misc/html.mdx)
- [drei Billboard](https://github.com/pmndrs/drei/blob/master/docs/abstractions/billboard.mdx)
- [R3F Scaling performance](https://r3f.docs.pmnd.rs/advanced/scaling-performance)
- [Html perf discussion (pmndrs/react-three-fiber #3130)](https://github.com/pmndrs/react-three-fiber/discussions/3130)
- [Axis Maps — Labeling and text hierarchy in cartography](https://www.axismaps.com/guide/labeling)
- [Mapbox — Guide to map design](https://www.mapbox.com/insights/map-design-process)
- [Making Effective Maps — Typography](https://colorado.pressbooks.pub/makingmaps/chapter/typography/)
