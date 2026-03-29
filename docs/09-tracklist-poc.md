# DiscoWorld: Tracklist Pipeline Proof-of-Concept

## Test: YOYAKU In-Store Session → Discogs → Stock Check

**Source:** YouTube video F8Nh7sJl4gU — YOYAKU in-store session
**Pipeline:** Parse tracklist → Discogs API lookup → match catalog number → check yoyaku.io stock

## Results

| # | Artist - Title | Label | Catno | Year | On YOYAKU? | Status |
|---|---|---|---|---|---|---|
| 1 | Ismistik - Lilladat 2 | Elektorni | ELKTRN005 | 2025 | **YES** | In stock |
| 2 | Tal Fussman - Sugar Lady | Time Passages | TP30 | 2025 | Partial | Artist known, release missing |
| 3 | B-Ai - Satisfy | Altered Circuits | ALT006 | 2024 | **YES** | In stock |
| 4 | RDS - Four Monsters | Undersound | USR035 | 2025 | **YES** | In stock |
| 5 | Radiation 30376 - Lost | Pinkman | PNKMN43 | 2021 | **OOS** | Out of stock |
| 6 | Kafkactrl - Morphing Blood | Distrito 91 | D91009 | 2024 | No | Not stocked |
| 7 | Promising Youngster - Cubo | GSVC | GSVC006 | 2025 | Partial | Artist known, VA comp missing |
| 8 | The Dexorcist - Text Drive | Bass Academy | TBA03 | 2017 | No | Not stocked |
| 9 | AUX88 - Bass Magnetic | Direct Beat | DBC4W-190 | 1993 | Partial | Artist known, this release missing |
| 10 | Aaron Carl - Down | Metroplex | M-035 | 1998 | **YES** | In stock |
| 11 | Marco Passarani - Dominion | SWOB | SWOB03 | 2025 | Partial | Artist known, release missing |
| 12 | Prince De Takicardie - Angel-a | Mulen | MULENV025 | 2025 | Partial | Artist known, release missing |
| 13 | BufoBufo - Bittern | Eudemonia | EUDEMONIA019 | 2025 | Partial | Artist known, release missing |
| 14 | Oh Mr James - I'm Not Here | Analogical Force | AF063 | 2025 | No | Not stocked |

## Summary

- **14/14** found on Discogs (100% identification rate)
- **4/14** in stock on YOYAKU (29%)
- **1/14** out of stock (restock opportunity)
- **6/14** artist known but specific release missing (ordering opportunity)
- **3/14** completely absent (new label discovery)

## Pipeline Insights

### Fuzzy Matching Needed
- Tracklist says "Text Drive", Discogs says "Test Drive" (The Dexorcist)
- Compilation tracks (VA) harder to match (Promising Youngster on GSVC Vol.6)
- Best match strategy: artist + catalog number > artist + title > title alone

### Ordering Opportunities (10 tracks)
Labels to source from distributors:
- **Distrito 91** (D91009) — KafkaCtrl
- **GSVC** (GSVC006) — Promising Youngster VA
- **Bass Academy** (TBA03) — The Dexorcist (2017, may be OOP)
- **Direct Beat** (DBC4W-190) — AUX88 classic, should be available
- **SWOB** (SWOB03) — Marco Passarani (2025, fresh)
- **Mulen** (MULENV025) — Prince De Takicardie (2025, fresh)
- **Eudemonia** (EUDEMONIA019) — BufoBufo (2025, fresh)
- **Analogical Force** (AF063) — Oh Mr James (2025, fresh)
- **Pinkman** (PNKMN43) — Radiation 30376 (restock)
- **Time Passages** (TP30) — Tal Fussman (2025, fresh)

### Next Step: Distributor Identification
For each label, find the distributor in:
1. YOYAKU's `distributormusic` taxonomy (WooCommerce)
2. Seb's supplier emails (if label is known)
3. Discogs label page → linked distributors
4. Manual lookup (for unknown labels)

## Validation
This PoC confirms the pipeline is technically viable. The 100% Discogs identification rate means the data quality is sufficient. The 29% in-stock rate means there's significant ordering upside from every in-store session.
