# Agent D — Spatial Layout Research

**Date:** 2026-04-17
**Mission:** spread 166 genres so they feel like cultural continents, not a floating blob.

---

## 1. Current state (measured, not guessed)

Measured on `yoyaku-server:/var/www/world.yoyaku.io/data/world.json`:

| Metric | Value | Implication |
|---|---|---|
| Genres | 166 | |
| Links (adjacency edges) | 185 | ~1.1 edges/node — sparse graph, most genres are "islands" |
| Scenes (coarse taxonomy) | 28 unique, top 10 capture ~90 genres | Scene = natural continent candidate |
| Biomes | 12 unique | Biome = already a curated semantic partition |
| **y range** | **0 → 0 (FLAT)** | "3D" is a lie — it's 2D rendered in 3D |
| x range | −41.7 → 41.6 (span ≈ 83) | |
| z range | −43.3 → 38.0 (span ≈ 81) | |
| Mean radial distance | 30.5 | genres cluster in a ring at r≈30, centered on origin |
| Min radial distance | 9.5 | Origin hole (empty center) |
| Max radial distance | 46.2 | Hard cap at WORLD_RADIUS=48 |
| Void ratio | Not computable (bbox vol=0) | Can only compute on 2D annulus |

**Reconstructed 2D annulus void ratio:** effective disc area = π·(46²) ≈ 6,647; total sphere cross-section ≈ Σ π·r² ≈ ~2,000 (depends on sphere sizes). → **~70 % of the accessible disc is empty.** Yet the disc itself only covers a fraction of a 2048² heightmap — in world coordinates (world radius ≈ 48 over a typical camera frustum 200+ units), **97 % of the visible scene is void.**

### Current pipeline (`packages/pipeline/genre_world_generator.py`)

1. Loads seed x/z positions from world.json (already hand-placed).
2. Runs **force-directed refinement** (`force_directed_refine`, 120 iters):
    - all-pairs repulsion (1/r² · 800)
    - link attraction (Hooke-like, 0.015 · weight)
    - scene centroid gravity (0.003 · α)
    - center gravity 0.002
    - DAMPING 0.92, clamps to WORLD_RADIUS=48
3. Voronoi tessellation on result → heightmap.

**Verdict:** this pipeline is symptomatic of the visual problem. `CENTER_GRAVITY=0.002` + `WORLD_RADIUS=48` + `REPULSION_STRENGTH=800` constrain every genre to a small puck. Scene gravity (0.003) is too weak to form continents. y=0 is hard-coded. No editorial seeds.

---

## 2. Algorithm survey

### 2.1 Dimension reduction (embedding → 2D/3D)

| Algo | Strengths | Weaknesses for our use | Fit |
|---|---|---|---|
| **UMAP** | Preserves both local (neighbors) AND global structure; stable; tuneable `n_neighbors`, `min_dist`; supports custom distance metrics; has `n_components=3` | Needs an embedding (vector per genre); stochastic | **Best pick** — what zig-zag.fm uses |
| t-SNE | Preserves local clusters beautifully | Destroys global structure; clusters float with no meaningful inter-distance; slower | **Reject** for continents |
| PCA | Linear, fast, deterministic | Linear only — genres relationships are non-linear | Use only as **initializer** for force layout |
| MDS (classical) | Preserves pairwise distances | Needs full dist matrix (166×166 OK); can't handle missing distances | Useful fallback if we can't build embeddings |
| Force-directed (d3, ngraph) | Uses graph structure directly (no embedding needed); interactive; well-understood | 185 edges on 166 nodes = under-connected; converges to disconnected islands that drift apart or collapse to center | Good for **post-processing** after UMAP, bad as primary |

### 2.2 Force-directed variants

- **d3-force** (JS): `forceSimulation().force('link', ...).force('charge', ...).force('x', ...).force('y', ...)`. Per-node `fx/fy` to pin anchors.
- **ngraph.forcelayout** (JS, n-D): faster, supports 3D (`dimensions: 3`). Better for our case if we keep 3D.
- **Python igraph / networkx** `spring_layout`: Kamada-Kawai or Fruchterman-Reingold. KK preserves graph-theoretic distance better — good for sparse adjacency.

### 2.3 Continent-shaping post-processing

| Technique | Purpose | Trade-off |
|---|---|---|
| **Voronoi partitioning** | Already used; turns point positions into territory polygons | Gives continents their shape but can't *create* continents if points are evenly spread |
| **Concave hull (α-shape) per scene** | Wraps each scene's genres in an organic outline → visible continent boundary | Needs enough points per scene; fallback for scenes with <4 genres |
| **Density-based rebalancing** | Compute local density ρ(x), push low-density points outward, compress high-density | Can break graph adjacency — run before force layout as init |
| **Anchor points + spring constraints** | Hand-pick canonical hubs ("Detroit techno", "Chicago house", "UK garage") at fixed lat/lon, let others settle around them via springs | Best narrative control; requires editorial list |
| **Gravitational wells per scene** | Each scene has its own center-of-mass pull; genre-to-scene gravity >> global center gravity | Matches "continent" metaphor directly; tune per-scene radius |
| **Lloyd's relaxation** | Iterative Voronoi smoothing — move each point to centroid of its cell | Makes cells more uniform in size; good for post-Voronoi cleanup |
| **Noise-displaced coastlines** | Already in pipeline (snoise2) — keep | — |

---

## 3. 3D vs 2D + altitude

**Recommendation: keep 2D positions, add altitude as 3rd axis.**

Rationale:
1. **zig-zag.fm is 2D for UX reasons**: a 2D map is navigable with mouse pan/zoom; a 3D cloud needs orbit controls and disorients users. Cultural geography (atlases, maps) is universally 2D in the human mental model.
2. **3D hides data**: with full 3D, near-viewer genres occlude far ones. Dense clusters become opaque blobs.
3. **Altitude as information channel** is richer than z-position:
    - y = f(log(trackCount), biome_elevation, scene_BPM)
    - peaks = popular/influential genres (techno, house)
    - valleys = niche (chiptune, eurotrash)
    - current pipeline already computes `BIOME_ELEVATION` (0.2–0.85) — unused in world.json, used only for heightmap.png
4. Keeps the `world.json.genres[i].y` slot meaningful instead of hard-coded 0.

**Hybrid: 2.5D.** x/z from layout algorithm, y from curated meta (trackCount log + biome bias + selection-time lift).

---

## 4. Editorial curation via seed anchors

Critical for making continents legible. We need ~8–12 **canonical hubs** pinned at stable positions. Candidates (to be validated with ben):

| Anchor | Scene | Proposed (x, z) | Role |
|---|---|---|---|
| `detroit-techno` | Techno | (−30, −20) | Techno continent nucleus |
| `chicago-house` | House | (20, 20) | House continent nucleus |
| `uk-garage` | UK Garage | (35, 0) | Bass continent bridge |
| `drum-n-bass` | Drum n Bass | (40, −30) | DnB peninsula |
| `ambient` | Ambient | (0, 40) | Ambient ocean |
| `chicago-acid` | Acid | (10, 15) | Acid bridge House↔Techno |
| `berlin-techno` | Techno | (−25, −30) | Techno twin-peak |
| `new-york-disco` | Disco/Pioneers | (25, 35) | Pioneers monument |
| `jungle` | Drum n Bass | (45, −20) | Jungle canopy |
| `industrial` | Industrial/Goth | (−40, 10) | Industrial wasteland pole |

**Algorithm:** pin anchors with `fx/fz` (fixed), run UMAP init → then force layout, non-anchors adjust freely. Anchors give scenes a **geographic identity** the user can memorize.

---

## 5. Proposed 3-phase rebuild pipeline

### Phase A — Embeddings (one-time, Python)

Source of similarity = **union of 3 signals**:

1. **Metadata embedding** (primary): text vector of `name + aka + description + scene + biome + emerged`. Use `sentence-transformers/all-MiniLM-L6-v2` (384-d, fast, offline). 166 genres × 384d = trivial.
2. **Link co-occurrence** (graph structure): 185 edges → adjacency matrix → node2vec (dim=64, walk_length=10, num_walks=40). Captures "who is next to whom" in curated links.
3. **Release co-tag similarity** (real data): from `release_particles.json` / `releases_preview.json` — for each release, list its genre tags → PMI matrix between genres.

**Final embedding = weighted concat:** `[0.5 * text_emb | 0.3 * node2vec | 0.2 * cotag_pmi]` → L2-normalize → 512-d vector per genre.

### Phase B — Projection (UMAP to 2D)

```python
import umap
reducer = umap.UMAP(
    n_neighbors=8,          # small — we want tight local clusters
    min_dist=0.15,          # bigger than default → breathing room
    n_components=2,
    metric='cosine',
    spread=2.0,             # wider spread → uses more canvas
    random_state=42,
)
coords_2d = reducer.fit_transform(embeddings)  # (166, 2)
```

**Knobs** (exposed in config):
- `n_neighbors`: 5 = many islands, 15 = blob. Start 8.
- `min_dist`: controls within-cluster tightness.
- `spread`: multiplier for total canvas — our "continent width".

### Phase C — Continent shaping (post-projection)

```python
# Step 1: scale to target canvas
coords = rescale(coords_2d, target_radius=120)  # was 48, go bigger

# Step 2: pin anchors (editorial)
ANCHORS = yaml.load('config/genre_anchors.yaml')  # 10 seeds
for slug, (x, z) in ANCHORS.items():
    idx = slug_to_idx[slug]
    coords[idx] = [x, z]
    fixed_mask[idx] = True

# Step 3: scene-aware force relaxation (replaces current force_directed_refine)
# - Scene gravity 10× stronger (0.03 not 0.003) to pull continent members together
# - Center gravity 0 (no longer needed, anchors hold structure)
# - WORLD_RADIUS = 150 (was 48)
# - Fixed anchors do not move; others relax for 200 iters
coords = force_relax_with_anchors(
    coords, fixed_mask, adjacency, scenes,
    iterations=200,
    scene_gravity=0.03,
    link_strength=0.015,
    repulsion=1500,
    center_gravity=0.0,
)

# Step 4: Lloyd relaxation (2 passes) to smooth Voronoi cell sizes
coords = lloyd_relax(coords, passes=2, mask=~fixed_mask)

# Step 5: compute altitude per genre (y axis)
# y = f(log(trackCount), biome_elevation, scene_BPM)
heights = compute_altitude(genres)  # returns y_i for each genre

# Step 6: concave hull per scene → continent polygon (for visual outlines)
continents = {}
for scene, members in scenes.items():
    if len(members) >= 4:
        continents[scene] = alpha_shape([coords[i] for i in members], alpha=0.3)
```

### Output schema (world.json diff)

```json
{
  "genres": [
    { "slug": "detroit-techno", "x": -30, "y": 12.4, "z": -20, "anchor": true, ... }
  ],
  "continents": [
    { "scene": "Techno", "polygon": [[x,z], ...], "centroid": [-27, -25], "color": "#..." }
  ]
}
```

---

## 6. d3-force JS snippet (client-side real-time tweak)

If we want users to "walk" genres interactively:

```js
import * as d3 from 'd3-force-3d'

const sim = d3.forceSimulation(genres)
  .numDimensions(2)  // 2D, y filled by altitude post-hoc
  .force('link', d3.forceLink(links).id(d => d.slug)
    .distance(d => 20 / (d.weight || 1))
    .strength(0.08))
  .force('charge', d3.forceManyBody().strength(-600))
  .force('scene', sceneGravity(scenes, 0.03))  // custom
  .force('anchor', anchorPin(ANCHORS))         // custom — sets fx/fz
  .force('collide', d3.forceCollide().radius(d => d.size + 2))
  .alphaDecay(0.02)
  .stop()

for (let i = 0; i < 300; i++) sim.tick()
```

Custom `sceneGravity`:
```js
function sceneGravity(scenes, k) {
  return alpha => {
    const centroids = {}
    scenes.forEach((members, scene) => {
      centroids[scene] = mean(members.map(m => [m.x, m.z]))
    })
    genres.forEach(g => {
      const [cx, cz] = centroids[g.scene]
      g.vx += (cx - g.x) * k * alpha
      g.vy += (cz - g.z) * k * alpha
    })
  }
}
```

---

## 7. Recommended pipeline — named files

```
discoworld/
├── config/
│   └── genre_anchors.yaml            # NEW — editorial seed positions (8-12 anchors)
├── packages/pipeline/
│   ├── build_genre_embeddings.py     # NEW — Phase A (text + node2vec + cotag)
│   ├── build_genre_layout.py         # NEW — Phase B (UMAP projection)
│   ├── shape_continents.py           # NEW — Phase C (anchor pin + force + Lloyd + hull)
│   ├── compute_altitude.py           # NEW — y axis from trackCount/biome/BPM
│   └── genre_world_generator.py      # REFACTOR — orchestrator only, calls above
├── scripts/
│   └── rebuild-world.sh              # NEW — pipeline runner (A→B→C→voronoi→heightmap)
└── packages/web/src/components/
    └── GenreWorld.jsx                # UPDATE — render continents polygon + altitude
```

**Execution order** (in `rebuild-world.sh`):
```bash
python -m packages.pipeline.build_genre_embeddings   # → data/embeddings.npy
python -m packages.pipeline.build_genre_layout       # → data/layout_2d.json
python -m packages.pipeline.shape_continents         # → data/world.json (x,z,anchor,continent)
python -m packages.pipeline.compute_altitude         # → patches world.json (y)
python -m packages.pipeline.genre_world_generator    # → heightmap, territories (existing)
```

**Config knobs exposed** (one YAML, not scattered constants):

```yaml
# config/layout.yaml
embeddings:
  text_weight: 0.5
  node2vec_weight: 0.3
  cotag_weight: 0.2
  node2vec_dim: 64

umap:
  n_neighbors: 8
  min_dist: 0.15
  spread: 2.0
  metric: cosine

continents:
  target_radius: 120          # was 48 — 2.5× expansion
  scene_gravity: 0.03         # was 0.003 — 10× stronger
  link_strength: 0.015        # keep
  repulsion: 1500             # up from 800
  center_gravity: 0.0         # off (anchors hold structure)
  iterations: 200
  lloyd_passes: 2

altitude:
  track_count_weight: 0.5     # log scaling
  biome_weight: 0.3
  bpm_weight: 0.2
  max_height: 20              # world units
```

---

## 8. Success criteria (measurable)

After rebuild, these should hold:

| Metric | Current | Target |
|---|---|---|
| World radius | 48 | 120 |
| Void ratio (in bounding disc) | ~70 % | 50–60 % (still breathable, not blob) |
| Scene intra-cluster mean dist / inter-cluster dist | ratio ≈ 0.9 (indistinct) | **< 0.45** (continents visible) |
| y variance | 0 | ≥ 3× max sphere radius |
| Anchored genres | 0 | 8–12 pinned |
| Continent polygon count | 0 | ≥ 8 (one per scene with ≥4 members) |

---

## 9. Implementation priority

1. **P0 (1 day):** `build_genre_layout.py` with UMAP + `shape_continents.py` with anchors. Replace existing `force_directed_refine` output. Visible impact: continents form.
2. **P1 (0.5 day):** `compute_altitude.py` → y-axis stops being zero. Camera re-angle in `GenreWorld.jsx`.
3. **P1 (0.5 day):** concave-hull continent polygons rendered as ground decals in Three.js.
4. **P2 (1 day):** `build_genre_embeddings.py` with real text + node2vec — currently anchors + adjacency alone will already look dramatically better, embeddings make it semantically defensible.

Total: ~3 days engineering. No model training, no GPU, all deterministic given anchors + seed.
