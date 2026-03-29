# DiscoWorld: Features & YOYAKU Ecosystem Integration

## Feature 1 — Dynamic Landing Page (No Login Required)

### Data Sources

**Discogs Data Dumps (monthly, free, CC0):**
- Masters dump has `have`, `want`, `rating` counts per release + genres/styles
- **Diff two monthly dumps → compute want velocity = "trending"**
- Genre distribution stats (releases per genre per year)
- "Most collected ambient albums of all time" = trivial single-dump query

**Discogs API (60 req/min, authenticated):**
- Search with sorting: `/database/search?sort=want&sort_order=desc&genre=Electronic&year=2025`
- Per-release: `community.have`, `community.want`, `community.rating`
- Marketplace stats: price, num_for_sale

**NOT available from Discogs:**
- No global "trending this week" feed
- No best sellers by genre
- No sales velocity
- No geographic heatmaps (no location data in dumps)

**Supplementary live data (scraping):**
| Source | Data | Access |
|--------|------|--------|
| Bandcamp | Daily best sellers, genre charts | Scrape |
| Beatport | Top 100 per genre, weekly | Scrape |
| Juno | Charts by genre | Scrape |
| RA | Reviews, recommended | Scrape |
| Boomkat | Bestsellers, staff picks | Scrape |

### Landing Page Sections

1. **"Most Wanted This Month"** — Discogs dump diff (biggest want-count jumps)
2. **"Rising Genres"** — Genre want velocity over time
3. **"Trending in [City]"** — Discogs + in-store session data combined
4. **"Latest In-Store Session"** — YOYAKU YouTube embed + mapped tracklist
5. **"Undervalued Gems"** — High rating + low price from marketplace API
6. **"Genre of the Week"** — Curated spotlight (editorial, like Boomkat)

**Best approach:** Discogs dumps for catalog depth + Bandcamp/Beatport scraping for real-time "hot" signals.

---

## Feature 2 — In-Store Sessions → Map

### How It Works

```
DJ plays at YOYAKU (filmed, uploaded to YouTube)
        ↓
Tracklist in YouTube description (timestamp + artist + title)
        ↓
Parser extracts tracks (regex: HH:MM:SS Artist - Title [Label])
        ↓
Each track → Discogs API search (/database/search?q=artist+title)
        ↓
Fuzzy matching layer (Levenshtein + label cross-reference)
        ↓
Matched releases get DiscoWorld coordinates
        ↓
"The DJ's Journey" = animated path on the map
        ↓
Each track node is clickable:
  • Play (YouTube timestamp link)
  • See on map (fly to position, see genre neighborhood)
  • Buy at YOYAKU (if in stock → direct link)
  • Request (if not in stock → demand signal)
```

### Reference: YOYAKU In-Store Sessions

Example video: https://www.youtube.com/watch?v=F8Nh7sJl4gU

Tracklist:
1. Ismistik - lilladat 2
2. Tal Fussman - Sugar Lady
3. B-Ai - Satisfy
4. RDS - Four Monsters
5. Radiation 30376 - Lost
6. Kafkactrl - Morphing Blood
7. Promising Youngster Feat. Huugen, Engy - Cubo
8. The Dexorcist - Text Drive
9. AUX88 - Bass Magnetic
10. Aaron Carl - Down (Eastside Mix)
11. Marco Passarani - Dominion
12. Prince De Takicardie - Angel-a
13. BufoBufo - Bittern
14. Oh Mr James - I'm Not Here (Analogical Force)

Labels identified:
- Pinkman, Analogical Force, Time Passages, Distrito 91, Elektorni Finland — all labels YOYAKU plausibly stocks/distributes
- AUX88 (Direct Beat), Aaron Carl (Wallshaker) — Detroit classics
- Promising Youngster "Cubo" — no Discogs match (fresh/unreleased press)

### YOYAKU Session Ecosystem

**Sessions live primarily on SoundCloud** (soundcloud.com/yoyaku), NOT YouTube.
15+ sessions archived with: Subb-an, MCDE, Mike Shannon, Tomoki Tamura, Edward, ERIS, E.LINA, Alex Albrecht, Christopher Ledger, Bertie, Lazerman, SIBIL, Jolly, Alina.
Tracklists are crowd-sourced on **set79.com**, not in YOYAKU's own descriptions.
Session archive page: yoyaku.io/artist/session/

### Competitor Content Strategies (CONFIRMED: nobody does tracklist→commerce)

- **Phonica Records**: Some YouTube, but NO shoppable tracklists. They sell Oh Mr James (AF063) on phonicarecords.com but don't connect it from video.
- **Hard Wax**: ZERO video/session strategy. Text-only recommendations.
- **Rush Hour**: SoundCloud-focused like YOYAKU. No tracklist-to-store linking.
- **Nobody links tracklists to commerce. This is a wide-open gap.**

The closest analogy is Shazam→Spotify, but for vinyl. YOYAKU would be first to close the loop between session content and e-commerce.

---

## Feature 3 — DJ Charts Integration

### Data Sources

**1001Tracklists:**
- Crowdsourced tracklists with timestamps, artist, title, label
- Auto-detect tracks from SoundCloud/YouTube via audio fingerprinting
- "Most played tracks" chart = DJ consensus metric
- No public API (would need to scrape or partner)

**Resident Advisor:**
- Monthly DJ Charts (curated top-10 picks — editorial taste, not play data)
- Club Charts (aggregated most-charted tracks)
- No public API. Cloudflare blocks scraping.

**Beatport:**
- Genre charts (top 100, sales-driven)
- Hype charts (emerging tracks)
- DJ charts (curated)
- No public API

**Key insight:** The highest-value data layer is connecting play frequency data (1001TL) with catalog identifiers (Discogs) and availability (YOYAKU stock). That triangle — **plays × catalog × stock** — is missing infrastructure nobody has built.

### DiscoWorld DJ Charts Feature

- Aggregate YOYAKU in-store session tracklists
- Cross-reference with Discogs for genre/label metadata
- Show "most played at YOYAKU this month" as a chart
- Each chart entry is a point on the map
- The chart becomes a "tour" of the DiscoWorld map

---

## Feature 4 — Supply Chain Pipeline (Play → Stock → Sell)

### Current Reality

Independent stores order vinyl via **email/phone**. Distributor sends weekly newsletter (PDF/Excel), store owner replies with quantities. Decision: gut feeling + DJ charts + customer requests.

**No APIs exist** in the independent electronic vinyl world. Clone, Rush Hour, Hardwax, Word and Sound, Kompakt — all email/PDF-based. No standardized format.

### The Missing Link

**Label → Distributor mapping does not exist as a public database.** This is tribal knowledge held by store buyers. Building this mapping = the key competitive moat.

### YOYAKU Already Has This Data

| System | Data Available |
|--------|---------------|
| yoyaku.io (WooCommerce) | `distributormusic` taxonomy = label→distributor mapping |
| yydistribution.fr (WooCommerce) | Supplier/label relationships, wholesale pricing |
| Objects (Odoo) | Full label contact data, manufacturing relationships |
| Parsify (supplier invoice parser) | 30+ distributor invoice templates learned |

**The label→distributor mapping already exists implicitly across these three systems.**

### The Automated Pipeline

```
Track identified in YOYAKU in-store session
        ↓
Discogs API → release → label
        ↓
Internal DB → label → distributor (from distributormusic taxonomy)
        ↓
Check stock on yoyaku.io (WooCommerce REST API)
        ↓
If NOT in stock:
  → Generate purchase suggestion (or auto-PO)
  → Quantity: 20-30 copies (configurable)
  → Email to supplier (seb@yoyaku.fr pipeline)
  → Or direct WooCommerce B2B order on yydistribution.fr
        ↓
When track arrives in stock:
  → Notification to DiscoWorld users who "wanted" it
  → Appears as "NEW" on the map
  → In-store session tracklist entry now says "In Stock"
```

### Why Nobody Else Can Do This

The bottleneck isn't technology — it's data:
1. **Track → Release:** Discogs API (anyone can do this)
2. **Release → Label:** Discogs API (anyone can do this)
3. **Label → Distributor:** Only YOYAKU has this (from 3 internal systems)
4. **Distributor → Purchase Order:** Only YOYAKU has automated supplier parsing
5. **Purchase Order → In-Stock Notification:** Only YOYAKU has the retail + discovery platform

**This is a 5-step pipeline that only YOYAKU can execute end-to-end.**

---

## Feature 5 — Discogs Collection as "Your Musical Passport"

### Flow

1. Connect Discogs (OAuth 1.0a)
2. Fetch collection (60 req/min, 100 items/page → 5000 records = <1 min)
3. Match to DiscoWorld coordinates
4. Generate "Your Musical Map" — a personal overlay on the globe

### What Users See

- Their collection as highlighted points on the map
- Heatmap of their taste (concentrated in Techno Massif? Spread across genres?)
- "Musical DNA" stats: % by genre, country, decade
- **Recommendations:** "Based on your collection, explore [this neighborhood]"
- **Shareable card:** "My DiscoWorld Passport" image for social media → virality

### Collection Analysis Outputs

| Metric | Derivation |
|--------|-----------|
| Genre distribution | Count releases per Discogs genre/style |
| Geographic spread | Release country metadata |
| Temporal range | Release year distribution |
| Collecting depth | Releases per label (do you deep-dive or skim?) |
| Rarity score | Avg want/have ratio of collection |
| Taste similarity | Compare collection vectors with other users |

---

## Integration Summary — The YOYAKU Flywheel

```
 ┌─────────────────────────────────────────────────┐
 │                  DISCOWORLD.FM                    │
 │                                                   │
 │  Landing (charts, trending, sessions)             │
 │          ↓                                        │
 │  Explore the map (genres, eras, geography)        │
 │          ↓                                        │
 │  Connect Discogs (personal map, recs)             │
 │          ↓                                        │
 │  Discover new tracks (in-store sessions, charts)  │
 │          ↓                                        │
 │  "Want" a track on DiscoWorld                     │
 │          ↓                                        │
 │  YOYAKU stocks it (supply chain automation)       │
 │          ↓                                        │
 │  Notification: "Now in stock at YOYAKU"           │
 │          ↓                                        │
 │  Purchase on yoyaku.io                            │
 │          ↓                                        │
 │  Track added to user's collection                 │
 │          ↓                                        │
 │  Map updates (personal map grows)                 │
 │          ↓                                        │
 │  Better recommendations → more discovery          │
 └─────────────────────────────────────────────────┘
```

**Every step feeds the next. This is a true flywheel that no competitor can replicate because it requires: discovery platform + retail + distribution + manufacturing under one roof.**
