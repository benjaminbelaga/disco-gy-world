# AGENT A — Design References for DiscoWorld Visual Refactor

**Mission:** Research visual design references for world.yoyaku.io (3D music exploration app — earth view, genre galaxy, planet detail). Deliver borrowable patterns and mood boards.
**Date:** 2026-04-17
**Ben's brief:** "less dark, more spaced, cultural-continent feel. Not clown-colour. Readable. Joyful but not loud." (see `memory/feedback_discoworld_visual.md`)

---

## 1. Reference-by-reference analysis

### 1.1 Every Noise at Once — everynoise.com

**URL:** https://everynoise.com/engenremap.html
**Creator:** Glenn McDonald (ex-Spotify) | ~6,291 genres plotted

**Background:** White / off-white. No imagery. Content IS the art.

**Typography on the map:** Uniform sans-serif. Critically, the **genre labels themselves ARE the data points** — text is the dot. Size varies by popularity (an under-documented fact: bigger text = more Spotify plays). No separate circles/markers; the label is the marker.

**Spacing philosophy:** Deliberately dense, "anti-design." Quote from our research: *"Deliberately simple interface that lets data dominate, avoiding trends while maximizing accessibility and exploration pathways."* No wasted whitespace — the map is ALWAYS full-bleed, edges-to-edges.

**Color:** Each genre gets a unique color derived algorithmically from three dimensions:
- **X axis:** "dense and atmospheric" (left) → "choppier, bouncier, sharper" (right)
- **Y axis:** "highly organic and acoustic" (bottom) → "highly synthetic and mechanized dance" (top)
- A third 'undefined' color dimension adds variance

The result: a cohesive-feeling rainbow where adjacent genres have visibly adjacent colors. Not random, not editorial — **derived from sound properties**.

**Navigation:** Click genre label → zooms into dedicated sub-genre map. Hover → 30-second Spotify preview plays. Click "»" arrow → loads a sub-scatter-plot of artists within that genre. Three modes: scan (map) / list / playlist.

**Emotional register:** Encyclopedic, democratic, curious. The line *"You Have Not Yet Heard Your Favourite Song"* captures it — awe at infinity, not mystery.

**Signature pattern:** Label-IS-point (no separate marker), color derived from acoustic features, hover-to-preview.

Source: [Information Is Beautiful Awards — Every Noise at Once](https://www.informationisbeautifulawards.com/showcase/260-every-noise-at-once), [engenremap.html](https://everynoise.com/engenremap.html)

---

### 1.2 Radiooooo — app.radiooooo.com

**URL:** https://app.radiooooo.com (redirects from radiooooo.com)
**Concept:** Time × place radio. Pick country + decade → curated playlist plays.

**Background:** Full-bleed Mercator world map. Historically beige/sepia paper-map treatment — evokes a 1930s atlas. (Current mobile app is darker, but the "paper globe" identity is core.)

**Typography:** Minimal. Decade dial uses a large numeric font (1900s → 2020s). Country hover shows country name in a serif or rounded sans. Understated — the MAP is the UI.

**Spacing philosophy:** Generous. One globe, one decade dial, one mood selector. Never more than 3 UI elements visible at once. The "4 o's in the name" itself signals playful abundance paired with minimal chrome.

**Color:** Country availability indicated by colored dots / filled country shapes. Mood selector uses three simple states ("slow / fast / weird") rendered as tactile toggles. Theme "island" pins (Hawaii, Neverland, 8-bit) add editorial color accents.

**Navigation primitives:**
- Globe pan/zoom (Mercator flat, not 3D)
- Click country → dropdown menu of decades available
- Decade dial → scrubs era
- Mood toggles → slow/fast/weird filter
- Theme islands → editorial playlists dotted ON the map

**Emotional register:** *"The music is curated with love, by humans for humans"* — a travelogue aesthetic. Warm, nostalgic, hand-made, joyful. Not mysterious. Not technical. The tagline was "the musical time machine."

**Signature pattern:** Use of the MAP itself as the primary UI (no sidebar filters), editorial "island pins" as curator playlists, minimal chrome.

Sources: [Open Culture on Radiooooo](https://www.openculture.com/2018/04/radiooooo-the-musical-time-machine.html), [Tedium: Le Globe Radiooooo](https://tedium.co/2017/04/03/le-globe-radiooooo-online-radio/), [Laughing Squid](https://laughingsquid.com/radiooooo-interactive-music-player/)

---

### 1.3 Music-Map — music-map.com

**URL:** https://www.music-map.com
**Creator:** Gnod project (pure ML similarity)

**Background:** Near-white. Utilitarian.

**Typography:** Plain sans-serif, uniform size. The only "design" move: proximity conveys similarity. Two artists close on screen = similar; far = dissimilar. That's the entire metaphor.

**Spacing philosophy:** Generous — the whole point is visible spacing AS the data. Each artist floats in relative isolation with whitespace around.

**Color:** None to speak of. All-black text on white.

**Navigation:** Search → map re-centers on that artist. Click any nearby artist → re-centers there. That's it. Radical simplicity.

**Emotional register:** *"Editorial discovery tool rather than a data dashboard — emphasizing elegant simplicity to encourage musical exploration."* Zero theatrics. Almost zen.

**Signature pattern:** Spatial distance = similarity (no color needed), monochrome is a feature not a bug, click-to-recenter as primary verb.

Source: [Music-Map.com](https://www.music-map.com/), [Laughing Squid](https://laughingsquid.com/interactive-music-map/)

---

### 1.4 zig-zag.fm — our closest competitor

**URL:** https://www.zig-zag.fm
**Team:** Hugo, Anto, Moritz (shared on r/TheOverload ~2025-12)
**Scale:** ~1.5M releases / 7-8M tracks from Discogs open data.

**Background:** **Cream / warm off-white** (~#E8E0D0 range). This is the biggest single insight from the reference set: they DELIBERATELY chose cream over black. It reads as cartographic / editorial, not sci-fi. Paper, not space.

**Typography on the map:** Labels for genres/subgenres are overlaid as text on the tile map. Labels include "Tech House", "Progressive House", "Deep Techno", "Dub Techno", "Tribal Techno". Decade labels ("1990s", "2020s") float at scale-appropriate positions. Labels fade/scale with zoom (LOD).

**Spacing philosophy:** Dense-but-organized. The map fills the viewport; genres are clustered into visually distinct continents with clear "seas" between them. No center-crammed cluster with empty margins (exactly our current problem).

**Color:** Per-subgenre color, but blended with weighted smoothing — adjacent genres bleed into each other like a topographic watercolor. The result is a small number of continent-scale hues (blue zone, red zone, green zone) rather than 166 separate clown colors. From our roadmap notes: *"Color per subgenre, blended by weights (smooth transitions between genre regions)."*

**Navigation primitives:**
- `deck.gl` 2D tile map (pan + zoom like Google Maps)
- Hover tile → popup with cover art + YouTube preview
- Paste YouTube/Discogs URL in search → zoom to that track
- "Gem" a track (community pin with comment)
- Layers menu (toggle arcs, connections)
- Filter by country/era/label
- Early-access gate: *"I have an access code / I don't have an access code"*

**Emotional register:** Editorial treasure map. Feels like a 19th-century atlas reinterpreted for techno. Serious but not cold. Inviting.

**Technical architecture (for reference):** Vector embeddings → matrix factorization on weighted metadata (label, era, region, subgenre, sound engineer, press plant, etc.) → UMAP projection to 2D → **big manual post-UMAP transformation to shape continents with cultural coherence**. The manual pass is key: pure UMAP is blobby; the hand-curated continents give it editorial identity.

**Signature pattern:** Cream background, smoothed continent-scale color blending, paste-URL-to-locate, manual post-UMAP cultural shaping.

Source: [zig-zag.fm](https://www.zig-zag.fm/), roadmap `memory/discoworld-roadmap.md` §zig-zag.fm benchmark.

---

### 1.5 Cosine.club — spectrogram similarity

**URL:** https://cosine.club
**Concept:** Cross-genre similarity via spectrogram cosine distance (not metadata).

**Background:** Clean light interface, grayscale-dominant.

**Typography:** Sans-serif throughout. Terminal/code treatment in FAQ (`$ cat`) — positioning as a hacker tool by music nerds.

**Spacing philosophy:** Content-hierarchy driven. Generous whitespace. **Does NOT visualize similarity in 2D/3D** — results are ranked lists. This is an important point: the spectrogram similarity is POWERFUL but the UI is INTENTIONALLY pedestrian. Form follows function.

**Color:** Minimal. Mostly grayscale with accents for interactive elements. Thumbnail album art provides visual variety.

**Navigation:** Track search → ranked similar-tracks list → embedded YouTube player. A "random gem" link for serendipity.

**Emotional register:** *"Technical-yet-approachable minimalism… a specialized tool built by music enthusiasts rather than a corporate platform — honest, functional, unpretentious."*

**Signature pattern:** Serious tool, quiet UI. No spatial metaphor. Proves that not every music-discovery product needs a map.

Source: [Cosine.club](https://cosine.club/)

---

### 1.6 Neal.fun — Neal Agarwal's generative experiences

**URL:** https://neal.fun
**Concept:** A gallery of one-off interactive experiences.

**Background:** Gallery is light / white. BUT the individual experiences use BACKGROUND AS NARRATIVE — e.g., "The Deep Sea" starts surface-blue and gradients into pitch black as you scroll down 10,000 meters; "The Size of Space" starts on Earth and gradients through the cosmos.

**Typography:** Clean sans-serif. Hand-drawn SVG tile thumbnails for each experience add whimsy. Each experience internally uses context-appropriate type.

**Spacing philosophy:** For the gallery — grid, airy. For each experience — full-bleed, scroll-driven, one idea per scroll distance. Extreme focus.

**Color:** Gallery is minimal. Experiences use **progressive color narratives**: Deep Sea = blue-to-black gradient mapped to depth. Size of Space = black-with-colored-celestial-accents. Color TELLS THE STORY.

**Navigation primitives:**
- Gallery: grid click → open experience
- Inside experiences: scroll is the primary verb. Scroll = time, scroll = distance, scroll = size.
- Minimal chrome inside experiences — just the subject.

**Emotional register:** *"Playful yet accessible. Balances approachability with intellectual curiosity rather than technical jargon, making complex ideas feel inviting and fun."* Joyful discovery. Childlike wonder. Zero cynicism.

**Signature pattern:** Scroll-driven narrative, one-idea-per-experience, color-as-story (gradient background that CHANGES as you move through scale/depth), hand-drawn whimsical icons.

Sources: [neal.fun](https://neal.fun/), [The Deep Sea](https://neal.fun/deep-sea/), [FlowingData on Deep Sea](https://flowingdata.com/2019/12/05/scroll-scroll-scroll-through-the-depths-of-the-ocean/)

---

### 1.7 Bonus reference: Casey Primozic's Music Galaxy

**URL:** https://cprimozic.net/blog/building-music-galaxy/
**Why bonus:** A 3D music visualization of ~70,000 artists. Directly analogous to DiscoWorld's genre-galaxy scene. Best single technical reference found.

**Background:** **No explicit background**. Depth is created by the artists and connections themselves. From the author: *"The majority of the galaxy's structure is made up of over 200,000 rendered connections between related artists."* Bloom post-processing makes the whole thing glow. The ETHER of the galaxy IS the artist connections.

**Typography (labels):** Sophisticated LOD system — quote: *"dynamic size scaling of labels so that further away labels get bigger as they approach"* + rendered *"opaque labels in order of furthest to closest so that z-indices worked out properly"* + *"culling off-screen labels for performance"* + label size scaled by artist popularity. **This is the label strategy DiscoWorld needs.**

**Spacing:** Not all 70k rendered at once — strategic visibility culling. Quality-tiering system per device.

**Color:** Rather than per-genre clown colors, uses a **3D noise function to vary color** — provides *"contrast and intrigue"* while *"making it easier to differentiate between the foreground and background."* User's personal top artists render in yellow/gold — "constellation-like" accent. Brilliant: 99% of points use a harmonious noise-varied palette; user's own data gets ONE accent color. Draws the eye.

**Navigation:** Free-fly through 3D space. Spatialized Web Audio — you hear nearby artists panned L/R. Playing artist's sphere pulses to music amplitude.

**Emotional register:** *"Ethereal, space-like vibe… cosmic mystery rather than cold technical visualization."*

**Signature pattern:** Bloom + noise-varied color + user-data-in-gold + spatialized audio + LOD labels. This is the template.

Source: [Building Music Galaxy — Casey Primozic](https://cprimozic.net/blog/building-music-galaxy/)

---

## 2. Cross-reference synthesis — 8 borrowable patterns

Ranked by likely impact for DiscoWorld given Ben's brief.

### Pattern 1 — Abandon pitch-black. Pick ONE of two bets.
Either **cream editorial** (zig-zag.fm) OR **deep-night-blue nebula with bloom** (Music Galaxy). NOT true black. Pitch-black is the current DiscoWorld anti-pattern. Ben's feedback file says it explicitly: *"the background void cannot be pitch-black."* Both options are proven. Pick one per view — possibly cream for earth view, nebula for genre-galaxy.

### Pattern 2 — Noise-varied color for 99% + one accent color for user's data
Stolen from Music Galaxy. Solves "clown-colour" problem directly: don't give 166 genres 166 random colors. Instead, use a **3D noise function** over spatial coordinates — adjacent genres get similar hues, creating visual continents organically. Reserve ONE accent color (yellow/gold, or DiscoWorld brand color) for user-relevant highlighting (their top genres, current city, selected track).

### Pattern 3 — Label-IS-point (Every Noise) OR LOD label scaling (Music Galaxy)
Two ways to solve the "unreadable labels" problem. Either make the label the dot (Every Noise: no marker, text IS the pin, size by popularity). Or do proper LOD: far labels smaller/faded, near labels bigger/opaque, always depth-sorted (Music Galaxy). DiscoWorld currently has tiny text floating near tiny spheres — worst of both worlds.

### Pattern 4 — Smoothed continent-scale color blending (zig-zag.fm)
UMAP projection + **manual post-transformation to carve continents with cultural coherence**. Then color by continent with weighted blending so adjacent tiles bleed into each other. This is THE "cultural continents" feel Ben asked for. The manual pass matters: pure ML gives blobs; curated continents give identity.

### Pattern 5 — Scroll/fly is the story (Neal.fun Deep Sea)
Narrative background gradient that CHANGES as camera moves. For DiscoWorld: earth view background could gradient from dawn-cream (camera close) to deep-indigo (camera far). Genre-galaxy scene could gradient from center-light to edge-dark as user flies through. Color is not a static choice — it's the TRIP.

### Pattern 6 — Editorial island pins for curated content (Radiooooo)
Don't just show the data. Sprinkle EDITORIAL islands on the map — curator-picked micro-scenes with distinct visual language. For DiscoWorld: YOYAKU's Objects press plant becomes an island. Sonar BCN becomes an island. Disquaire friends become islands. Gives map warmth + commerce tie-in.

### Pattern 7 — Paste URL to locate (zig-zag.fm + Reddit u/Okieboy2008)
Paste YouTube or Discogs URL in search → map zooms to that track. DiscoWorld already ships this for Discogs as of `1b0b2da` — confirms the pattern works; verify YouTube path works too.

### Pattern 8 — Minimum chrome, maximum map (all refs)
Every single reference keeps UI chrome to 2-3 elements max. Radiooooo = globe + decade dial + mood toggle. Every Noise = map + hover preview. Zig-zag.fm = map + layers + search. DiscoWorld currently has onboarding modal, layer controls, minimap, player, search bar, filters, coords, year slider — 8+ UI elements. Audit for things to hide behind a single "more" affordance.

### Pattern 9 (bonus) — Spatialized audio
Music Galaxy pans audio L/R based on 3D position of the playing artist relative to camera. DiscoWorld already plays YouTube audio centered — adding spatial panning is a ~50-line Web Audio API change that would DRAMATICALLY increase the "I'm inside a galaxy" feel.

### Pattern 10 (bonus) — Label overlay technology choice
Use HTML-overlay labels (drei `<Html>`) instead of in-scene `<Text>` when legibility > depth. HTML labels are pixel-sharp, respect browser font rendering, and are trivially styled with backdrop blur / pill backgrounds. Already noted in Ben's feedback file.

---

## 3. Three mood board directions

### Direction A — "Treasure Atlas"  (cream editorial — zig-zag.fm descendant)
Cream-beige background (~#E8E0D0). Genre continents rendered as topographic watercolor blobs with hand-drawn coastline feel. Typography: a humanist sans or a warm serif (Söhne Halbfett or GT Sectra) for continent names in LARGE type; a condensed grotesk for subgenre labels in small type. A single gold/ochre accent for the user's current location. Evokes: Radiooooo × 19th-century atlas × zig-zag.fm. Joyful, editorial, inviting. **Best fit for earth view** (globe + cities already has geographic metaphor).

### Direction B — "Night Library" (deep-blue nebula with bloom — Music Galaxy descendant)
Deep indigo-to-near-black radial gradient (~#0B0F2E center fading to ~#030515 edges), NEVER pure black. Bloom post-processing on genre spheres. Noise-varied color across spheres creates natural clusters (no 166 clown colors). Gold for user's current track/genre. Typography: a luminous grotesk (Neue Haas Grotesk or Inter) rendered with slight glow via CSS `text-shadow: 0 0 8px` on HTML overlay labels. Evokes: night sky observatory × Music Galaxy × serene research. **Best fit for genre-galaxy view** (cosmic metaphor earned).

### Direction C — "Warm Drift" (Neal.fun scroll-narrative hybrid)
Background gradient that MORPHS with camera distance/view — cream at the outermost zoom, dusk-orange mid-zoom, deep indigo at planet-detail zoom. Subtle, never jarring. This ties all three views (earth/genre-galaxy/planet) into one continuous emotional journey: surface → atmosphere → depth. Typography: warm rounded sans throughout (Basis Grotesque or GT Walsheim). Hand-drawn editorial icons for curator islands (Radiooooo-style). Evokes: Neal.fun Deep Sea × Radiooooo × Sunday morning record-digging. **Best fit for a unified three-view experience** — and best answer to Ben's brief holistically: "joyful but not loud."

---

## 4. Top-3 steals (most actionable)

**1. STEAL CREAM BACKGROUND + MANUAL CONTINENTS from zig-zag.fm.**
The single biggest lever. Flips the emotional register from "sci-fi dark" to "editorial atlas" instantly. Requires: swap background gradient; group genres by existing `scene`/`biome` fields into 8-12 continents; render continent-scale labels LARGER than subgenre labels. Likely 2-3 days of work for an immediate 80% improvement in the "legibility + joyful" axes of Ben's brief.

**2. STEAL NOISE-VARIED COLOR + GOLD USER ACCENT from Music Galaxy.**
Solves "clown-colour" directly. Adjacent genres get harmonious colors via 3D noise over position. Reserve gold for user's track / current city / dig-path trail. One-day refactor of the color assignment in `GenreWorld.jsx`. Immediately ships the "coloured but not clown" target.

**3. STEAL LOD LABEL STRATEGY from Music Galaxy.**
Quote worth pinning to the PR: *"dynamic size scaling of labels so that further away labels get bigger as they approach… opaque labels in order of furthest to closest… culling off-screen labels… label size based on artist popularity."* Exactly the four rules DiscoWorld is missing. Switch to drei `<Html>` overlay labels for subgenres with a `useFrame` distance check + opacity LOD + pill backdrop for contrast on whatever background we pick. Single-day refactor, delivers the "readable without hovering" requirement from Ben's brief directly.

---

## Appendix — sources

- [zig-zag.fm](https://www.zig-zag.fm/) — direct competitor, cream + UMAP continents
- [Every Noise at Once](https://everynoise.com/engenremap.html) | [Information Is Beautiful Awards entry](https://www.informationisbeautifulawards.com/showcase/260-every-noise-at-once) — Glenn McDonald, label-IS-point, 6k+ genres
- [Radiooooo](https://app.radiooooo.com/) | [Open Culture review](https://www.openculture.com/2018/04/radiooooo-the-musical-time-machine.html) | [Tedium feature](https://tedium.co/2017/04/03/le-globe-radiooooo-online-radio/) — globe + era dial + mood toggle
- [Music-Map.com](https://www.music-map.com/) — pure proximity = similarity, monochrome
- [Cosine.club](https://cosine.club/) — spectrogram similarity, minimalist UI
- [neal.fun](https://neal.fun/) | [Deep Sea](https://neal.fun/deep-sea/) — scroll-driven narrative, background as story
- [Casey Primozic — Building Music Galaxy](https://cprimozic.net/blog/building-music-galaxy/) — 70k-artist 3D galaxy, bloom + noise color + LOD labels + spatial audio
- Internal: `memory/feedback_discoworld_visual.md`, `memory/discoworld-roadmap.md` §zig-zag.fm benchmark
