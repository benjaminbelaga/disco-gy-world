# DiscoWorld: World Design Document

## 1. World Structure — Volcanic Atoll (Ring + Archipelago)

The planet is a **volcanic atoll** — a massive ring-shaped landmass surrounding a central ocean called the **Source Sea**. The ring represents time flowing outward: the inner coastline = 1960s (ancient ruins), the outer edge = the present.

Genre families form **archipelago clusters** connected by land bridges and ferry routes.

**Why this structure wins:**
- Adjacency = musical proximity (house and techno share a coastline)
- Sub-genres are neighborhoods within an island
- The ring naturally encodes history without forcing a flat timeline
- The Source Sea contains the **Deep Listening Abyss** — ambient/drone territory accessible only by "diving"

---

## 2. Terrain-to-Sound Mapping

| Musical Property | Terrain Property |
|---|---|
| **BPM** | Elevation. 70 BPM dub = sea level. 140 jungle = mountain peaks. 170+ gabber = volcanic summits |
| **Energy/Darkness** | Temperature + weather. Dark techno = perpetual overcast. Disco = tropical sun |
| **Harmonic complexity** | Vegetation density. Minimal = desert. Jazz house = lush gardens |
| **Age of genre** | Geological depth. Detroit techno = exposed bedrock. Future bass = fresh topsoil |
| **Release volume** | Territory area + building density |
| **Influence** | Rivers flowing downhill from influential genres into derivative ones |

---

## 3. Biome Map — Core Territories

### Techno Massif
Basalt mountain range, perpetual thunderstorms, brutalist bunkers carved into cliffs.
- **Detroit Foundry** — industrial ruins, cyan wireframe towers, abandoned auto plants
- **Berlin Wall** — concrete labyrinth, Berghain-style slabs, strobe-only lighting
- **Dub Techno Fog Basin** — perpetual mist, echo chambers, Basic Channel minimalism

### House Plains
Golden savanna, warm breeze, open-air pavilions.
- **Chicago South Side** — the ancient capital, warehouse temples
- **Deep House Hot Springs** — underground thermal pools, warm amber glow
- **Tech House Plaza** — shared park between Techno Massif and House Plains

### Ambient Depths
Underwater realm beneath the Source Sea. Bioluminescent caves. No buildings, only currents and coral formations.

### Trance Highlands
Crystal spires, aurora-lit sky, perpetual twilight.
- **Goa** — overgrown temple district, tropical decay
- **Psytrance Peaks** — hallucinogenic mushroom forest

### Jungle Canopy
Massive trees with cities built into branches.
- **DnB Upper Canopy** — fast, chaotic, neurofunk wiring
- **Ragga Jungle Lower Canopy** — warm, rhythmic, gold accents

### Industrial Wasteland
Volcanic flats, sulfur vents, metal foundries.
- **EBM Factory District** — Front 242, assembly lines
- **Noise Caldera** — the volcano itself, pure destruction

### Disco Riviera
Coastal resort, mirror-ball lighthouses, boardwalks.
- **Italo Harbor** — old port, chrome and pastel
- **Nu-Disco Waterfront** — renovated, modern glass

### Dubstep Rift
Canyon splitting the southern continent. Purple-lit, bass tremors visible.
- **Deep Dubstep Abyss** — sub-pressure, dark meditation
- **Post-Dubstep Bridges** — spanning the rift, experimental

### IDM Crystalline
Geometric crystal formations on eastern cliffs. Algorithmic, self-replicating.
- **Autechre Maze** — non-Euclidean architecture
- **Warp Campus** — The Designers Republic aesthetic

### Minimal Garden
Zen rock garden plateau. Sparse, clean, every element precisely placed.
- **Kompakt Courtyard** — pristine white, single accent objects

---

## 4. City View — Buildings as Data

| Property | Visual Encoding |
|---|---|
| Building **height** | Number of releases that year |
| Building **style** | Genre culture (concrete=Berlin techno, mirrored glass=progressive house, hand-painted tiles=Balearic) |
| **Roads** | Collaboration/sample connections between artists |
| **Parks** | Genre intersection spaces |
| **Decay** | Declining genres show weathering, cracks, overgrowth |

---

## 5. Temporal Evolution

Slide a time dial:
- **1960s**: Empty planet, only Source Sea and monoliths (Stockhausen, Silver Apples)
- **1980s**: First settlements glow on inner ring — Chicago, Detroit, Düsseldorf
- **1990s**: Explosive expansion outward. Trance crystals erupt. Jungle canopy grows overnight
- **2000s**: Some districts crumble (big-room trance), new rifts open (dubstep), minimal garden is meticulously raked
- **2020s**: Megacity density. Genre borders blur. Hyperpop = glitching holographic district that doesn't obey physics

**Shader-based animation:** Each building has a `birthYear` attribute. Vertex shader: `scale.y = smoothstep(birthYear, birthYear+2, currentYear) * targetHeight`. GPU-side, zero CPU overhead. Scrubbing timeline = updating one uniform → entire world responds instantly.

---

## 6. Game Design Philosophy

**Civilization meets Breath of the Wild:**
- Civ's **tech tree = genre tree** (explore influences to unlock territories)
- BotW's **biome exploration** = distinct weather, sound, physics per territory
- Discovery-driven, not objective-driven
- The player is a **radio signal** traveling through the world

**No Man's Sky inspiration:** Procedural neighborhood generation from Discogs data — release counts, years, and connections seed the terrain algorithmically.
