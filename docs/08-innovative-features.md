# DiscoWorld: Innovative Features Roadmap

## Tier 1 — MVP Differentiators (Phase 1)

### "Describe a Vibe" — Natural Language Map Search
**The killer feature.** No competitor does this.

User types: "dark hypnotic techno that sounds like driving at 3am"
→ System embeds the query into genre vector space
→ Lands on the corresponding map region (Dub Techno Fog Basin)
→ Releases in that region start playing

**Tech:** OpenAI/Claude embeddings on Discogs style tags + genre descriptions from our taxonomy. Text → vector → nearest map region. Straightforward.

**Why it wins:** Makes the map accessible to casual users who don't know genre names.

### Temporal Exploration — "Berlin 1993"
**Time machine for music.**

Cross-reference: release year + label city + genre = "what was being released in Berlin in 1993?"
→ Navigate to that moment on the map
→ See what existed, what was emerging, what was dying
→ The map breathes and changes as you scrub time

**Tech:** Discogs has release dates and label locations. Pre-computed per-year snapshots.

### Crate Neighbors — "Who Digs Like Me?"
**Social stickiness from day 1.**

Discogs collections are public API data. Compute Jaccard similarity between collections.
→ "You and @technohead share 47 releases. Your collections diverge in the Ambient Depths."
→ Map overlay showing overlap zones and divergence zones

**Tech:** Jaccard similarity on collection sets. O(n) per user pair, cacheable.

---

## Tier 2 — Viral / Engagement (Phase 2)

### Taste Distance — Shareable Metric
"Ben and Alex are 4.7 genres apart."

One number = the average map distance between two users' collection centroids.
→ Shareable card (like Spotify Wrapped) → virality
→ Compare with friends, DJs, strangers

### DJ Transition Suggestions
"What bridges Track A to Track B?"

Using BPM + genre + year + map proximity (no audio analysis for v1).
→ DJs would kill for this
→ v2: integrate cosine.club API for audio-based bridging

### Record Store QR → Map
**Low-tech, high-impact.** Any store prints a QR code linking to `discoworld.fm/release/{discogs_id}`.
→ Customer scans in-store → sees the release on the map → explores neighbors
→ Zero API needed, just URL scheme
→ Creates physical → digital loop

---

## Tier 3 — Gamification (Non-Gimmicky)

### Explorer Badges
Reward the behavior vinyl people ALREADY do:

| Badge | Criteria |
|-------|---------|
| **Deep Digger** | Found 10 releases with <50 Discogs wants |
| **Genre Polyglot** | Explored 10+ genre territories |
| **Time Traveler** | Listened to tracks from 5+ different decades |
| **Continent Hopper** | Visited all major biomes |
| **Taste Pioneer** | First to "gem" a release that later gets 100+ wants |

Leaderboards rank **discovery breadth**, not listening volume.

### Year in DiscoWorld
Annual recap (like Spotify Wrapped but for discovery):
- "You explored 14 territories"
- "Your deepest dig: [obscure release]"
- "Your taste shifted 2.3 genres toward Ambient this year"
- Shareable card → annual viral moment

---

## Tier 4 — Defer to Phase 3+

| Feature | Why defer |
|---------|----------|
| Sample detection | Requires audio analysis infrastructure |
| Store inventory crowdsourcing | Cold start problem, needs critical mass |
| Label territory claiming | Business development, not just code |
| Listening rooms (real-time) | Complex sync, low ROI until userbase |
| "Currently pressing" | Cool but niche (Phase 4, YOYAKU integration) |

---

## Priority for MVP Launch

1. **Describe a vibe** (the hook — makes first visit magical)
2. **3D world with timeline** (the wow factor — visual differentiation)
3. **Discogs collection import** (personal investment — retention)
4. **Crate neighbors** (social — word-of-mouth growth)
5. **YouTube playback** (utility — actually hear the music)

These five features create a product that's genuinely new, not a remix of existing tools. Everything else builds on top.
