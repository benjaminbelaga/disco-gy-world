# DiscoWorld: Visual Culture per Genre

## Genre Visual Identities & 3D Translation

### Detroit Techno
- **Aesthetic:** Afrofuturist sci-fi. Underground Resistance militant graphics, Drexciya underwater Atlantis mythology
- **Key artists:** Abdul Qadim Haqq (UR sleeve art)
- **Colors:** Deep blue, silver, cyan, black
- **3D:** Sleek dark towers with cyan wireframe edges, hovering geometric structures, starfield skybox. Buildings like spacecraft — angular, reflective, sparse

### Chicago House
- **Aesthetic:** Raw, soulful, urban. Trax/DJ International hand-drawn sleeves, warehouse interiors
- **Colors:** Warm orange, gold, brown, red
- **3D:** Brick warehouses with glowing amber windows, steam vents, warm streetlights. Low-rise, dense, human-scale. Disco ball reflections on wet pavement

### Berlin Techno
- **Aesthetic:** Brutalist, monochrome, post-industrial. Tresor vault, Basic Channel minimalism, Berghain concrete
- **Key artists:** Konrad Black (Minus)
- **Colors:** Grey, black, dark green, hazard yellow
- **3D:** Massive concrete bunkers, exposed rebar, fog. No ornamentation. Towering slabs with minimal openings

### UK Rave / Acid House
- **Aesthetic:** Smiley faces, day-glo rave flyers (Pez, Junior Tomlin), pirate radio chaos
- **Colors:** Fluorescent yellow/pink/green on black
- **3D:** Open fields with scattered warehouse shells, neon laser beams cutting fog, chaotic stacked sound systems

### Jungle / DnB
- **Aesthetic:** Metalheadz skull logos, urban grit, Jamaican sound system culture, graffiti
- **Colors:** Dark green, gold, red, black
- **3D:** Dense urban blocks, graffiti-covered walls, dark alleyways. Gold accents on dark surfaces. Rain

### Trance / Goa
- **Aesthetic:** Psychedelic fractals, Alex Grey-style sacred geometry, Tipper visuals
- **Colors:** Purple, teal, cosmic blue, neon green
- **3D:** Crystalline temples, fractal trees, aurora skies. Translucent structures. Everything breathing/morphing

### IDM / Warp
- **Aesthetic:** The Designers Republic (TDR), glitch art, algorithmic
- **Key artists:** The Designers Republic, Alexander Rutterford (Autechre videos)
- **Colors:** Clinical white, neon accents, digital artifacts
- **3D:** Clean white geometries with glitch distortion zones. Grid-precise but periodically corrupted

### Dubstep / Bass
- **Aesthetic:** Hyperdub/Tempa artwork, dark, subaquatic, London nocturnal
- **Colors:** Deep purple, dark blue, black
- **3D:** Subterranean caverns, low-frequency waveform terrain, bioluminescent accents

### Minimal / Microhouse
- **Aesthetic:** Kompakt white-space design (Total series), geometric simplicity
- **Key artists:** Stefan Marx (Smallville)
- **Colors:** White, light grey, single accent color
- **3D:** Sparse white cubes, generous negative space. One carefully placed coloured object per block

### Industrial / EBM
- **Aesthetic:** Machine aesthetics, factory imagery, Throbbing Gristle/SPK confrontation
- **Colors:** Rust, gunmetal, dark red, black
- **3D:** Rusted factories, grinding gears, smokestacks, chain-link. Hostile, mechanical

### Synthwave / Retrowave
- **Aesthetic:** 80s retro-futurism, perspective grids, chrome text, sunset gradients
- **Colors:** Magenta, cyan, orange
- **3D:** Neon grid ground plane, chrome palm trees, sunset horizon. Everything has bloom/glow

---

## Audio-to-Visual Mapping

| Audio Property | Visual Encoding |
|---|---|
| BPM | Building density / movement speed |
| Energy/loudness | Building height + light intensity |
| Bass weight | Ground-level fog density + camera shake |
| Harmonic complexity | Colour saturation + particle count |
| Mood (major/minor) | Colour temperature (warm/cool) |
| Reverb/space | Draw distance + atmospheric haze |

## Key Visual Artists / References

- **The Designers Republic** (Warp Records)
- **Abdul Qadim Haqq** (Underground Resistance / Detroit)
- **Konrad Black** (Minus / Minimal)
- **Stefan Marx** (Smallville / Hamburg)
- **Non-Format** (various electronic labels)
- **Hassan Rahim** (dark/experimental)
- **Alexander Rutterford** (Autechre videos)
- **Robert Henke** (laser installations / Monolake)
- **Ryoji Ikeda** (data sculpture)

## Audio-Reactive Principles

Winamp AVS/Milkdrop → FFT spectral data mapped to shader parameters. Same principle for DiscoWorld:
- Real-time audio features drive world properties (fog, colour, particle emission, geometry deformation)
- Web Audio API `AnalyserNode` → frequency bins → shader uniforms
- YouTube IFrame API blocks audio data (CORS) — need server-side beat detection for YouTube tracks
