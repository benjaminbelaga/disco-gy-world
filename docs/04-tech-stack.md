# DiscoWorld: Tech Stack Decisions

## Final Stack

```
Vite + React + React Three Fiber (R3F) + drei + Zustand + leva + custom shaders
```

No deck.gl. No Next.js.

---

## Decision Rationale

### Frontend Framework: Vite + React (NOT Next.js)

Next.js adds SSR complexity with zero benefit for a 3D app — WebGL can't SSR. You'd `dynamic(() => import(...), { ssr: false })` everything anyway. Vite + React gives faster HMR, simpler config, no hydration issues.

SvelteKit + threlte is viable but the ecosystem is 10x smaller — fewer examples, fewer plugins.

SEO: Use a static landing page with meta tags; the 3D app itself is a SPA.

### 3D Engine: React Three Fiber (NOT raw Three.js)

R3F adds React's component model with negligible overhead — the render loop is pure Three.js. For a data-viz project with UI panels, filters, timeline controls alongside 3D, R3F's declarative approach saves massive boilerplate.

### deck.gl: SKIP

The @deck.gl/three integration exists but is clunky — shared WebGL context works but you fight two rendering pipelines. For terrain+buildings, custom shaders on BufferGeometry will outperform deck.gl's layer abstraction and give full creative control.

### State Management: Zustand

R3F standard. Key pattern: store slices for `camera`, `timeline`, `filters`, `playback`, `selection`.

**Critical:** Never put per-frame animation state in React state — use refs or Zustand's `subscribe` with `transient` updates to avoid React re-renders. Timeline position updates 60x/sec via ref, React only re-renders for discrete UI changes.

---

## Performance Benchmarks

### InstancedMesh Limits
| Count | Performance |
|-------|-----------|
| 10K instances | Trivial, 60fps |
| 100K instances | Solid 60fps with frustum culling |
| 1M instances | Needs custom BufferGeometry with manual attribute management |

At 1M points: single geometry with position attributes + custom shaders.

### Post-Processing
Bloom adds ~2-4ms per frame at 1080p. Use **selective bloom** (layers) — only glow active/selected buildings, not the whole scene. `@react-three/postprocessing` wraps pmndrs/postprocessing (much faster than Three.js built-in EffectComposer).

---

## Asset Pipeline

### Heightmaps
Pre-generate as 16-bit PNGs from data offline (Node script). Load as displacement maps. One heightmap per "region."

### Texture Atlases (Album Covers)
Pack album covers into 4096x4096 atlases (TexturePacker or custom script). UV-map buildings to atlas coordinates. Load ~10 atlases instead of 1000 individual images.

### KTX2/Basis Compression
Use `KTX2Loader` with basis_transcoder.wasm — 4-6x smaller than PNG, GPU-native decompression. drei's `<useKTX2>` handles this. Pre-convert with `toktx` CLI.

---

## Audio Integration

Web Audio API's `AnalyserNode` gives FFT data. Pass frequency bins as uniforms to shaders each frame — cheap (one `getByteFrequencyData` call).

**YouTube caveat:** IFrame API cannot expose audio data (CORS-blocked). For YouTube playback, sync visuals to beat-detection done server-side, stored as timestamp arrays.

For owned audio: direct `<audio>` element + Web Audio = full FFT access.

---

## Deployment

**Self-host or Vercel Static Export:**
- Vercel static works — no serverless needed
- 3D assets (KTX2, GLB, heightmaps) on CDN (Cloudflare R2 = cheapest)
- Self-hosting advantage: no bandwidth limits on asset serving
- Self-hosted server with sufficient capacity

---

## Mobile Strategy

Expect 30fps max on mid-range phones with 100K+ objects.

| Strategy | Implementation |
|----------|---------------|
| Adaptive resolution | `<AdaptiveDpr>` auto-reduces |
| Adaptive events | `<AdaptiveEvents>` reduces raycasting |
| LOD | Simplified geometry at distance |
| Instance cap | 10K on mobile (aggregate small buildings) |
| Touch controls | drei `<OrbitControls>` handles pinch-zoom natively |
| Detection | `navigator.maxTouchPoints > 0` |

---

## Key Libraries

| Library | Role |
|---------|------|
| `@react-three/fiber` | React Three.js renderer |
| `@react-three/drei` | Helpers (Billboard, Html, Environment, AdaptiveDpr, Instances, Preload) |
| `@react-three/postprocessing` | Bloom, selective glow, effects |
| `zustand` | State management |
| `leva` | Dev controls/debug |
| `gsap` | Camera animations, transitions |
| `three` | Core 3D engine |

---

## Reference Projects

| Project | Tech | Relevance |
|---------|------|-----------|
| [Lusion v3](https://lusion.co) | Three.js + custom shaders | Awwwards SOTY 2023. Premium 3D standard |
| [Music Galaxy](https://cprimozic.net/blog/building-music-galaxy/) | Three.js + WebAudio | 70K Spotify artists as 3D point cloud |
| [Bruno Simon](https://bruno-simon.com) | Three.js + Cannon.js | Gamified 3D navigation |
| [GitHub Globe](https://github.blog/2020-12-21-how-we-built-the-github-globe/) | Custom WebGL | Data globe with arcs |
| [Globe.GL](https://globe.gl) | Three.js wrapper | Open-source data globe |
| [THREE.Terrain](https://github.com/IceCreamYou/THREE.Terrain) | Three.js | Procedural terrain generation |
| [Procedural City](https://medium.com/@Rototu/making-a-procedural-skyscraper-city-generator-with-three-js-and-webgl2-8f8b721bd044) | Three.js + WebGL2 | Shader-based skyscrapers |
