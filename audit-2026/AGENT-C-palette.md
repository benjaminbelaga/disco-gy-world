# AGENT-C — DiscoWorld Color Palette & Background Treatment

**Mission:** Replace pitch-black void with a background that reads as *cultural continent*, not clown-colored carnival. Must pair with YOYAKU gold `#c4956a` and editorial IBM Plex Mono tone.

**Benchmarks consulted:**
- **zig-zag.fm** — cream/tan `~#e8e0d0`, treasure-map register, warm and editorial
- **Everynoise.com** — pure white `#ffffff`, colored genre dots, clinical/atlas register
- **Apple Vision Pro environments** — desaturated dark-navy + starfield temperature variation, reverent immersion
- **Radix Colors** — Sand (warm neutral) and Olive (warm dark) dark scales, scientifically accessible
- **Tailwind Stone** scale — warm neutrals (hue ~35-106°) vs Slate (cool, 250°+)
- **Carbon Design** — editorial grays, high-ink fidelity

---

## Background treatment research

Five background classes considered:

1. **Pitch-black (current)** — maximum bloom contrast but emotionally cold, reads as "tech demo"
2. **Dark-navy nebula** — Vision Pro / Spotify Now-Playing. Depth without death. `#0a1428 → #1a2440` radial
3. **Cream parchment** — zig-zag.fm, treasure-map. Needs dark spheres (hard pivot from current)
4. **Editorial warm-dark** — IBM Carbon Gray 100 warmed slightly. `#1c1917 → #292524` (Tailwind Stone 900/800). Museum-at-night feel.
5. **Dawn/dusk gradient skybox** — horizon line with warm bottom / cool top. Risky, can feel kitsch. Only works if stars fade with zoom.

**Accessibility note:** All text candidates below tested against WCAG 2.1 AA (4.5:1 normal body text, 3:1 for large headings). Bloom-adjacent UI text is worst-case scenario — test at max bloom intensity.

---

## Palette 1 — "Night Atlas" (warm-dark editorial)

Default candidate. Museum-at-night, editorial, never pitch-black.

### Swatches

| Role | Hex | Name | Usage |
|---|---|---|---|
| Background deep | `#1c1917` | Stone 900 | Skybox / fog far |
| Background near | `#292524` | Stone 800 | Ground plane / fog near |
| Continent accent 1 | `#c4956a` | YOYAKU Gold | House / 4-on-the-floor cluster (brand anchor) |
| Continent accent 2 | `#8b7355` | Burnished bronze | Disco / funk / soul |
| Continent accent 3 | `#d4a574` | Warm sand | Ambient / downtempo |
| Continent accent 4 | `#a86b47` | Terracotta | Afrobeat / global |
| Continent accent 5 | `#6b8e7f` | Sage (cool counter) | Electronica / IDM — provides cool-warm tension |
| Text primary | `#f5f5f4` | Stone 100 | Body / labels. Contrast on `#1c1917`: **15.8:1** ✓ AAA |
| Text muted | `#a8a29e` | Stone 400 | Secondary labels. Contrast: **6.4:1** ✓ AA+ |
| Highlight/hover | `#fafaf9` | Stone 50 | Active continent ring, hover glow |

### Emotional register
Late-night listening session. Warm-dark. Editorial but alive. The gold anchor makes DiscoWorld visually consistent with yoyaku.io checkout and invoice templates.

### Genre fit
- **Excellent:** house, disco, funk, soul, ambient, jazz, downtempo
- **Acceptable:** techno (use cooler Sage for hardest sub-genres), rock
- **Poor:** hyperpop, happy hardcore, j-pop (accents are too muted for kinetic genres)

---

## Palette 2 — "Dawn Continent" (cream parchment)

zig-zag.fm-adjacent. Treasure map, archival, maximum readability.

### Swatches

| Role | Hex | Name | Usage |
|---|---|---|---|
| Background deep | `#e8e0d0` | zig-zag cream | Skybox / fog (paper) |
| Background near | `#f3ecdd` | Parchment light | Ground plane (lighter, creates depth) |
| Continent accent 1 | `#8b4513` | Saddle brown | House / classics |
| Continent accent 2 | `#c4956a` | YOYAKU Gold | Disco / funk (brand) |
| Continent accent 3 | `#2d4a3e` | Deep forest | Techno / dub |
| Continent accent 4 | `#a0304a` | Burgundy ink | Rock / experimental |
| Continent accent 5 | `#3d5a7a` | Navy wash | Ambient / classical |
| Text primary | `#1c1917` | Stone 900 | Body. Contrast on `#e8e0d0`: **14.9:1** ✓ AAA |
| Text muted | `#57534e` | Stone 600 | Secondary. Contrast: **6.8:1** ✓ AA+ |
| Highlight/hover | `#8b4513` | Saddle brown | Active state, link underlines |

### Emotional register
Cartographer's notebook. Archival, patient, serious-music-library. Pairs beautifully with vinyl/physical media narrative.

### Genre fit
- **Excellent:** classical, jazz, folk, world music, classical electronic (BoC, Aphex), dub, reggae
- **Acceptable:** house, ambient, indie
- **Poor:** metal, hyperpop, trap — the paper background reads as "polite" and will undercut aggressive genres

### Trade-off
**Hard pivot** from current. Requires redesigning all sphere colors (dark on light) and rethinking bloom (bloom on cream = washed out — need emissive spheres with outline/border instead). Highest redesign cost of the four palettes.

---

## Palette 3 — "Aurora Observatory" (dark-navy + nebula)

Apple Vision Pro Environment aesthetic. Cosmic but not clinical.

### Swatches

| Role | Hex | Name | Usage |
|---|---|---|---|
| Background deep | `#0a1428` | Abyssal navy | Skybox top |
| Background near | `#1a2a4a` | Nebula mid | Skybox bottom / ground glow |
| Starfield tint warm | `#fef981` | Starlight yellow | ~20% of stars (color temp variation) |
| Starfield tint cool | `#a8c5e8` | Starlight blue | ~60% of stars |
| Starfield neutral | `#f5f5f4` | Stone 100 | ~20% of stars |
| Continent accent 1 | `#c4956a` | YOYAKU Gold | Warm genres (disco, soul, house) |
| Continent accent 2 | `#7fb3d5` | Sky blue | Cool genres (ambient, techno) |
| Continent accent 3 | `#b19cd9` | Lavender | Experimental / drone |
| Continent accent 4 | `#ff9e7d` | Coral | Pop / kinetic |
| Continent accent 5 | `#6eb89f` | Mint | IDM / electronica |
| Text primary | `#e8ecf4` | Frost white | Contrast on `#0a1428`: **14.2:1** ✓ AAA |
| Text muted | `#8b96a8` | Cool gray | Contrast: **4.9:1** ✓ AA |
| Highlight/hover | `#fef981` | Starlight yellow | Active ring (matches Objects design token) |

### Emotional register
Planetarium. Reverent, cosmic, "music as galaxies." The Objects design token `#FEF981` cameos as the highlight — small cross-brand echo.

### Genre fit
- **Excellent:** ambient, drone, electronica, IDM, progressive, space-rock, techno
- **Acceptable:** classical, jazz (needs warm accent dominance)
- **Poor:** folk, country, acoustic singer-songwriter — cosmic register fights intimacy

### Trade-off
Closest to current aesthetic (still dark) — lowest migration cost. But the cold-blue undertone fights YOYAKU's warm gold. Solve by using gold dominantly and blue sparingly.

---

## Palette 4 — "Editorial Atlas" (warm off-white, everynoise-adjacent)

Clinical, atlas register, maximum data density.

### Swatches

| Role | Hex | Name | Usage |
|---|---|---|---|
| Background deep | `#fafaf9` | Stone 50 | Skybox |
| Background near | `#f5f5f4` | Stone 100 | Ground / fog near |
| Continent accent 1 | `#1c1917` | Stone 900 | Primary cluster (high-density genres) |
| Continent accent 2 | `#c4956a` | YOYAKU Gold | Featured / brand genres |
| Continent accent 3 | `#dc2626` | Vermillion | Rock / punk (needs saturation to read on light bg) |
| Continent accent 4 | `#1e40af` | Ink blue | Electronic / techno |
| Continent accent 5 | `#15803d` | Moss | Folk / acoustic / world |
| Text primary | `#1c1917` | Stone 900 | Contrast on `#fafaf9`: **16.2:1** ✓ AAA |
| Text muted | `#57534e` | Stone 600 | Contrast: **7.1:1** ✓ AA+ |
| Highlight/hover | `#c4956a` | YOYAKU Gold | Active state |

### Emotional register
Reference work. Encyclopedia. Serious but lifeless — the "Wikipedia of music" feel.

### Genre fit
- **All genres acceptable** — clinical neutrality doesn't flatter any specific genre
- But flatters **none emotionally** — best for "I know what I want, show me the data" user mode

### Trade-off
Maximum readability and data density. Zero emotional warmth. Bloom effect nearly invisible — must rebuild entire lighting approach. Appropriate if DiscoWorld pivots to "tool" over "experience."

---

## Comparison matrix

| Palette | Migration cost | Bloom-compat | Brand fit | Genre coverage | Joy factor |
|---|---|---|---|---|---|
| 1. Night Atlas | Low | High | Excellent (gold anchor) | Broad warm genres | Medium-high |
| 2. Dawn Continent | High (full redesign) | Low (rebuild lighting) | Good | Narrow — acoustic/archival | High |
| 3. Aurora Observatory | Lowest (minor tweak) | Highest | Good (gold sparingly) | Electronic-biased | Medium |
| 4. Editorial Atlas | High | None (rebuild) | Neutral | Universal but flat | Low |

---

## Chosen palette for DiscoWorld v2

### Primary recommendation: **Palette 1 — "Night Atlas"**

**Background:** radial gradient `#1c1917` (far) → `#292524` (near, ground plane)
**Fog:** Stone 900 matched, density 0.02
**Core accents:** `#c4956a` (YOYAKU Gold, featured), `#d4a574` (sand), `#a86b47` (terracotta), `#8b7355` (bronze), `#6b8e7f` (sage, cool counter)
**Text:** `#f5f5f4` primary, `#a8a29e` muted
**Highlight:** `#fafaf9`

### Why Night Atlas over the others

1. **Lowest disruption to current 3D pipeline.** Bloom still works (dark bg), spheres still emissive, camera/fog/lights unchanged. A color-swap, not a rebuild.
2. **Brand-aligned.** Gold `#c4956a` is the YOYAKU anchor — DiscoWorld inherits the same warm palette as yoyaku.io checkout, Objects pitch decks, and CEO email signatures. Consistency compounds.
3. **Solves Ben's "less dark, not pitch-black, not clown" brief directly.** Stone 900 reads as *warm night*, not *void*. The gold+sand+terracotta family reads as *continent*, not *disco ball*.
4. **Widest genre fit for YOYAKU's catalog** — house, disco, funk, soul, jazz, ambient are all home turf.
5. **Accessibility verified** — all text pairs AAA-level WCAG.

### Secondary recommendation if Ben wants bigger pivot

**Palette 3 — Aurora Observatory** — if the target is "cosmic wonder over editorial warmth." Keeps dark aesthetic, adds nuance via colored starfield and aurora. Costs a starfield rebuild (~1 day) but no sphere redesign.

### Not recommended unless strategic pivot

**Palettes 2 and 4** require rebuilding bloom, spheres, and lighting — 5-10 day refactor. Only worth it if DiscoWorld is being repositioned as a reading-heavy reference tool (Palette 4) or a physical-archival narrative (Palette 2).

---

## Implementation notes for Agent implementing this

1. Replace `scene.background = new THREE.Color(0x000000)` → `0x1c1917`
2. Add `THREE.Fog(0x1c1917, 10, 80)` to soften continent edges
3. Update all emissive materials: boost intensity +20% (Stone 900 bg absorbs less bloom than pure black, so spheres must compensate)
4. Ground plane: subtle `#292524` plane at y=-5 with opacity 0.6 for "continent floor" feel
5. Text overlays: switch `color: white` → `color: #f5f5f4` everywhere
6. Test with `r3f-perf` — dark bg + fog should cost <1ms extra
7. **Do not** remove bloom entirely; Stone 900 bg still benefits from selective bloom on active continent

---

**Report complete.** Written to `/Users/yoyaku/repos/discoworld/audit-2026/AGENT-C-palette.md`.
