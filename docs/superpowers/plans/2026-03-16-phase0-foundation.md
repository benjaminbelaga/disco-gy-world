# Phase 0: Foundation — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the unified data foundation that all subsequent phases depend on — taxonomy bridge, style co-occurrence matrix, release-per-genre counts, and content-based similarity index.

**Architecture:** Python pipeline scripts process the existing Discogs dump (4.87M electronic releases JSONL) and Ishkur dataset (166 genres, 185 links) into a unified SQLite database. FastAPI endpoints serve the unified data. No frontend changes in this phase.

**Tech Stack:** Python 3.12, SQLite, FastAPI, pandas (data processing), scikit-learn (sparse vectors), IGTEM26 JSON

**Spec:** `docs/superpowers/specs/2026-03-16-discoworld-v2-mega-design.md` sections 3.3, 4.2 Phase 1, 7

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `packages/pipeline/taxonomy_bridge.py` | Map Discogs 106 styles ↔ Ishkur 166 genres (many-to-many) |
| `packages/pipeline/style_cooccurrence.py` | Build style co-occurrence matrix from releases JSONL |
| `packages/pipeline/genre_population.py` | Count releases per genre using taxonomy bridge |
| `packages/pipeline/similarity_index.py` | Pre-compute content-based release neighbors (385K vinyl) |
| `packages/pipeline/build_db.py` | Orchestrator: run all pipeline steps, output unified SQLite |
| `packages/pipeline/db_schema.sql` | SQLite schema definition |
| `packages/api/db.py` | SQLite connection helper for FastAPI |
| `packages/api/routes/recommendations.py` | GET /api/recommendations/{release_id} |
| `packages/api/routes/releases.py` | GET /api/releases?genre=&style=&country=&year= |
| `packages/pipeline/tests/test_taxonomy_bridge.py` | Tests for taxonomy mapping |
| `packages/pipeline/tests/test_cooccurrence.py` | Tests for co-occurrence matrix |
| `packages/pipeline/tests/test_similarity.py` | Tests for similarity index |

### Modified Files
| File | Change |
|------|--------|
| `packages/api/main.py` | Add router imports for new endpoints |
| `packages/web/public/data/world.json` | Enrich genre nodes with release_count from pipeline |

### Data Files (generated, not committed)
| File | Contents |
|------|----------|
| `data/discoworld.db` | Unified SQLite database |
| `data/taxonomy_bridge.json` | Discogs style → Ishkur genre mapping |
| `data/style_cooccurrence.json` | Style pair co-occurrence weights |

---

## Chunk 1: Taxonomy Bridge

### Task 1: Download IGTEM26 dataset

**Files:**
- Create: `packages/pipeline/data/igtem26/` (directory)

- [ ] **Step 1: Clone IGTEM26 repo and extract genre data**

```bash
cd /Users/yoyaku/repos/discoworld
git clone https://github.com/eskoNBG/IGTEM26.git /tmp/igtem26
cp /tmp/igtem26/data/*.json packages/pipeline/data/igtem26/
ls packages/pipeline/data/igtem26/
```

Expected: JSON files with 251 genres, 502 connections, GeoJSON polygons

- [ ] **Step 2: Explore IGTEM26 data structure**

```bash
cd /Users/yoyaku/repos/discoworld
python3 -c "
import json
with open('packages/pipeline/data/igtem26/genres.json') as f:
    data = json.load(f)
print(f'Genres: {len(data)}')
print(f'Sample: {json.dumps(data[0], indent=2)[:500]}')
"
```

- [ ] **Step 3: Commit**

```bash
git add packages/pipeline/data/igtem26/
git commit -m "data: add IGTEM26 genre dataset (251 genres, 502 edges)"
```

### Task 2: Build taxonomy bridge mapping

**Files:**
- Create: `packages/pipeline/taxonomy_bridge.py`
- Create: `packages/pipeline/tests/test_taxonomy_bridge.py`

- [ ] **Step 1: Write failing test for taxonomy bridge**

```python
# packages/pipeline/tests/test_taxonomy_bridge.py
import pytest
from taxonomy_bridge import build_bridge, get_genres_for_style, get_styles_for_genre

def test_bridge_maps_house_style():
    bridge = build_bridge()
    genres = get_genres_for_style(bridge, "House")
    assert len(genres) > 0
    assert any("house" in g.lower() for g in genres)

def test_bridge_maps_techno_style():
    bridge = build_bridge()
    genres = get_genres_for_style(bridge, "Techno")
    assert len(genres) > 0
    assert any("techno" in g.lower() for g in genres)

def test_bridge_covers_all_discogs_styles():
    bridge = build_bridge()
    # All 106 Discogs electronic styles should have at least one mapping
    unmapped = [s for s in bridge["discogs_styles"] if not bridge["style_to_genres"].get(s)]
    assert len(unmapped) <= 10, f"Too many unmapped styles: {unmapped}"

def test_bridge_is_bidirectional():
    bridge = build_bridge()
    # Every mapped genre should have at least one style
    for genre in bridge["genre_to_styles"]:
        assert len(bridge["genre_to_styles"][genre]) > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/yoyaku/repos/discoworld/packages/pipeline
python3 -m pytest tests/test_taxonomy_bridge.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'taxonomy_bridge'`

- [ ] **Step 3: Write taxonomy bridge implementation**

```python
# packages/pipeline/taxonomy_bridge.py
"""
Taxonomy Bridge: Maps Discogs styles ↔ Ishkur/IGTEM26 genres.

Strategy:
1. Load IGTEM26 genres (251 genres with names, aka, sceneId)
2. Load Discogs styles from stats.json (106 electronic styles)
3. Fuzzy match: normalize names, match by substring/alias
4. Manual overrides for ambiguous cases
5. Output: bidirectional many-to-many mapping
"""
import json
from pathlib import Path
from difflib import SequenceMatcher

DATA_DIR = Path(__file__).parent / "data"

# Manual overrides for styles that don't fuzzy-match well
MANUAL_OVERRIDES = {
    "Acid": ["Acid House", "Acid Techno", "Acid Trance"],
    "Breaks": ["Breakbeat", "Nu Breaks"],
    "Euro House": ["Eurodance"],
    "Leftfield": ["IDM", "Experimental Electronic"],
    "Synth-pop": ["Synthpop"],
    "New Beat": ["New Beat"],
    "Rhythmic Noise": ["Power Noise", "Industrial"],
    "Sound Collage": ["Experimental Electronic"],
    "Musique Concrete": ["Experimental Electronic"],
    "Abstract": ["IDM", "Experimental Electronic"],
    "Noise": ["Noise", "Power Electronics"],
}


def normalize(name: str) -> str:
    return name.lower().strip().replace("-", " ").replace("&", "and")


def load_igtem26_genres() -> list[dict]:
    for filename in ["genres.json", "genrebiglabels.json"]:
        path = DATA_DIR / "igtem26" / filename
        if path.exists():
            with open(path) as f:
                return json.load(f)
    # Fallback: load from existing world.json
    world_path = Path(__file__).parent.parent / "web" / "public" / "data" / "world.json"
    if world_path.exists():
        with open(world_path) as f:
            data = json.load(f)
        return data.get("genres", [])
    raise FileNotFoundError("No genre data found")


def load_discogs_styles() -> list[str]:
    stats_path = DATA_DIR.parent / "data" / "processed" / "stats.json"
    if stats_path.exists():
        with open(stats_path) as f:
            stats = json.load(f)
        return list(stats.get("styles", {}).keys())
    # Fallback: hardcoded top styles
    return [
        "House", "Techno", "Trance", "Ambient", "Drum n Bass",
        "Electro", "Downtempo", "Synth-pop", "Industrial", "IDM",
        "Breakbeat", "Acid", "Deep House", "Minimal", "Dub Techno",
        "Progressive House", "Progressive Trance", "Hardcore",
        "Gabber", "Happy Hardcore", "UK Garage", "Dubstep", "Grime",
        "Trip Hop", "Experimental", "Noise", "Dark Ambient",
        "Leftfield", "Euro House", "Italo-Disco", "Hi NRG",
        "EBM", "Acid House", "Tech House", "Breaks",
    ]


def fuzzy_match(style: str, genres: list[dict], threshold: float = 0.6) -> list[str]:
    norm_style = normalize(style)
    matches = []
    for genre in genres:
        name = genre.get("name", "")
        norm_name = normalize(name)
        # Exact match
        if norm_style == norm_name:
            matches.append(name)
            continue
        # Substring match
        if norm_style in norm_name or norm_name in norm_style:
            matches.append(name)
            continue
        # Check aliases
        for aka in genre.get("aka", "").split(","):
            if normalize(aka.strip()) == norm_style:
                matches.append(name)
                break
        # Sequence matcher
        ratio = SequenceMatcher(None, norm_style, norm_name).ratio()
        if ratio >= threshold:
            matches.append(name)
    return list(set(matches))


def build_bridge() -> dict:
    genres = load_igtem26_genres()
    styles = load_discogs_styles()

    style_to_genres = {}
    genre_to_styles = {}

    for style in styles:
        # Check manual overrides first
        if style in MANUAL_OVERRIDES:
            mapped = MANUAL_OVERRIDES[style]
            style_to_genres[style] = mapped
        else:
            matched = fuzzy_match(style, genres)
            style_to_genres[style] = matched if matched else [style]

    # Build reverse mapping
    for style, genre_list in style_to_genres.items():
        for genre in genre_list:
            if genre not in genre_to_styles:
                genre_to_styles[genre] = []
            if style not in genre_to_styles[genre]:
                genre_to_styles[genre].append(style)

    return {
        "discogs_styles": styles,
        "igtem26_genres": [g.get("name", "") for g in genres],
        "style_to_genres": style_to_genres,
        "genre_to_styles": genre_to_styles,
    }


def get_genres_for_style(bridge: dict, style: str) -> list[str]:
    return bridge["style_to_genres"].get(style, [])


def get_styles_for_genre(bridge: dict, genre: str) -> list[str]:
    return bridge["genre_to_styles"].get(genre, [])


def save_bridge(output_path: Path | None = None):
    bridge = build_bridge()
    path = output_path or DATA_DIR.parent / "data" / "taxonomy_bridge.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(bridge, f, indent=2)
    print(f"Taxonomy bridge saved: {len(bridge['style_to_genres'])} styles mapped")
    return bridge


if __name__ == "__main__":
    save_bridge()
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/yoyaku/repos/discoworld/packages/pipeline
python3 -m pytest tests/test_taxonomy_bridge.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/pipeline/taxonomy_bridge.py packages/pipeline/tests/test_taxonomy_bridge.py
git commit -m "feat: taxonomy bridge — Discogs styles ↔ Ishkur genres mapping"
```

### Task 3: Build style co-occurrence matrix

**Files:**
- Create: `packages/pipeline/style_cooccurrence.py`
- Create: `packages/pipeline/tests/test_cooccurrence.py`

- [ ] **Step 1: Write failing test**

```python
# packages/pipeline/tests/test_cooccurrence.py
import pytest
from style_cooccurrence import build_cooccurrence

def test_cooccurrence_returns_pairs():
    # Use a small test dataset
    test_releases = [
        {"styles": ["House", "Deep House"]},
        {"styles": ["House", "Acid House"]},
        {"styles": ["Techno", "Acid"]},
        {"styles": ["House", "Deep House", "Acid House"]},
    ]
    matrix = build_cooccurrence(test_releases)
    assert ("House", "Deep House") in matrix or ("Deep House", "House") in matrix

def test_cooccurrence_counts_are_correct():
    test_releases = [
        {"styles": ["House", "Deep House"]},
        {"styles": ["House", "Deep House"]},
        {"styles": ["Techno"]},
    ]
    matrix = build_cooccurrence(test_releases)
    pair = tuple(sorted(["House", "Deep House"]))
    assert matrix[pair] == 2

def test_single_style_releases_excluded():
    test_releases = [{"styles": ["Techno"]}]
    matrix = build_cooccurrence(test_releases)
    assert len(matrix) == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/yoyaku/repos/discoworld/packages/pipeline
python3 -m pytest tests/test_cooccurrence.py -v
```

Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# packages/pipeline/style_cooccurrence.py
"""
Build a style co-occurrence matrix from Discogs releases.
Counts how often two styles appear together on the same release.
This creates weighted edges between styles in the genre graph.
"""
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def build_cooccurrence(releases: list[dict] | None = None) -> dict[tuple, int]:
    if releases is None:
        releases = load_releases()

    pair_counts = Counter()
    for release in releases:
        styles = release.get("styles", [])
        if len(styles) < 2:
            continue
        for pair in combinations(sorted(set(styles)), 2):
            pair_counts[pair] += 1

    return dict(pair_counts)


def load_releases():
    """Stream releases from JSONL file."""
    jsonl_path = DATA_DIR / "processed" / "electronic_releases.jsonl"
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Releases file not found: {jsonl_path}")
    with open(jsonl_path) as f:
        for line in f:
            yield json.loads(line)


def save_cooccurrence(output_path: Path | None = None, top_n: int = 1000):
    matrix = build_cooccurrence()
    # Sort by count descending, take top N pairs
    sorted_pairs = sorted(matrix.items(), key=lambda x: -x[1])[:top_n]
    result = {f"{a}|{b}": count for (a, b), count in sorted_pairs}

    path = output_path or DATA_DIR / "style_cooccurrence.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Co-occurrence matrix saved: {len(result)} pairs")
    return result


if __name__ == "__main__":
    save_cooccurrence()
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/yoyaku/repos/discoworld/packages/pipeline
python3 -m pytest tests/test_cooccurrence.py -v
```

Expected: All PASS

- [ ] **Step 5: Run on real data (smoke test)**

```bash
cd /Users/yoyaku/repos/discoworld/packages/pipeline
python3 -c "
from style_cooccurrence import build_cooccurrence, load_releases
from itertools import islice
releases = list(islice(load_releases(), 10000))
matrix = build_cooccurrence(releases)
top = sorted(matrix.items(), key=lambda x: -x[1])[:10]
for pair, count in top:
    print(f'{pair}: {count}')
"
```

Expected: Top pairs like `('House', 'Deep House')`, `('Techno', 'Minimal')` etc.

- [ ] **Step 6: Commit**

```bash
git add packages/pipeline/style_cooccurrence.py packages/pipeline/tests/test_cooccurrence.py
git commit -m "feat: style co-occurrence matrix from Discogs releases"
```

### Task 4: Genre population counts

**Files:**
- Create: `packages/pipeline/genre_population.py`

- [ ] **Step 1: Write implementation**

```python
# packages/pipeline/genre_population.py
"""
Count releases per genre using the taxonomy bridge.
Enriches world.json genres with release_count from Discogs dump.
"""
import json
from collections import Counter
from pathlib import Path
from taxonomy_bridge import build_bridge

DATA_DIR = Path(__file__).parent.parent / "data"


def count_releases_per_genre(releases=None, bridge=None):
    if bridge is None:
        bridge = build_bridge()
    if releases is None:
        from style_cooccurrence import load_releases
        releases = load_releases()

    genre_counts = Counter()
    for release in releases:
        styles = release.get("styles", [])
        for style in styles:
            mapped_genres = bridge["style_to_genres"].get(style, [])
            for genre in mapped_genres:
                genre_counts[genre] += 1

    return dict(genre_counts)


def enrich_world_json(genre_counts: dict, world_json_path: Path | None = None):
    path = world_json_path or Path(__file__).parent.parent / "web" / "public" / "data" / "world.json"
    with open(path) as f:
        world = json.load(f)

    for genre in world.get("genres", []):
        name = genre.get("name", "")
        genre["release_count"] = genre_counts.get(name, 0)

    with open(path, "w") as f:
        json.dump(world, f, indent=2)
    print(f"Enriched {len(world['genres'])} genres with release counts")


if __name__ == "__main__":
    counts = count_releases_per_genre()
    top = sorted(counts.items(), key=lambda x: -x[1])[:20]
    print("Top 20 genres by release count:")
    for genre, count in top:
        print(f"  {genre}: {count:,}")
    enrich_world_json(counts)
```

- [ ] **Step 2: Run on sample data**

```bash
cd /Users/yoyaku/repos/discoworld/packages/pipeline
python3 -c "
from genre_population import count_releases_per_genre
from style_cooccurrence import load_releases
from itertools import islice
releases = list(islice(load_releases(), 50000))
counts = count_releases_per_genre(releases)
top = sorted(counts.items(), key=lambda x: -x[1])[:10]
for g, c in top: print(f'{g}: {c}')
"
```

- [ ] **Step 3: Commit**

```bash
git add packages/pipeline/genre_population.py
git commit -m "feat: genre population counts from Discogs dump via taxonomy bridge"
```

### Task 5: SQLite database schema + builder

**Files:**
- Create: `packages/pipeline/db_schema.sql`
- Create: `packages/pipeline/build_db.py`

- [ ] **Step 1: Write schema**

```sql
-- packages/pipeline/db_schema.sql
-- DiscoWorld unified database

CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    scene TEXT,
    biome TEXT,
    bpm_min INTEGER,
    bpm_max INTEGER,
    emerged TEXT,
    year INTEGER,
    release_count INTEGER DEFAULT 0,
    description TEXT
);

CREATE TABLE IF NOT EXISTS genre_links (
    source_id INTEGER REFERENCES genres(id),
    target_id INTEGER REFERENCES genres(id),
    weight REAL DEFAULT 1.0,
    link_type TEXT DEFAULT 'influence',
    PRIMARY KEY (source_id, target_id)
);

CREATE TABLE IF NOT EXISTS taxonomy_bridge (
    discogs_style TEXT NOT NULL,
    genre_id INTEGER REFERENCES genres(id),
    confidence REAL DEFAULT 1.0,
    PRIMARY KEY (discogs_style, genre_id)
);

CREATE TABLE IF NOT EXISTS style_cooccurrence (
    style_a TEXT NOT NULL,
    style_b TEXT NOT NULL,
    count INTEGER NOT NULL,
    PRIMARY KEY (style_a, style_b)
);

CREATE TABLE IF NOT EXISTS releases (
    id INTEGER PRIMARY KEY,
    discogs_id INTEGER UNIQUE,
    title TEXT NOT NULL,
    artist TEXT,
    label TEXT,
    catno TEXT,
    country TEXT,
    year INTEGER,
    format TEXT,
    styles TEXT,  -- JSON array
    youtube_url TEXT
);

CREATE TABLE IF NOT EXISTS release_neighbors (
    release_id INTEGER REFERENCES releases(id),
    neighbor_id INTEGER REFERENCES releases(id),
    score REAL NOT NULL,
    PRIMARY KEY (release_id, neighbor_id)
);

CREATE INDEX IF NOT EXISTS idx_releases_year ON releases(year);
CREATE INDEX IF NOT EXISTS idx_releases_country ON releases(country);
CREATE INDEX IF NOT EXISTS idx_releases_label ON releases(label);
CREATE INDEX IF NOT EXISTS idx_release_neighbors_score ON release_neighbors(score DESC);
```

- [ ] **Step 2: Write build orchestrator**

```python
# packages/pipeline/build_db.py
"""
Orchestrator: runs all pipeline steps and builds unified SQLite database.

Usage: python3 build_db.py [--sample N] [--skip-similarity]
"""
import argparse
import json
import sqlite3
from pathlib import Path
from itertools import islice

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "discoworld.db"


def create_db():
    conn = sqlite3.connect(DB_PATH)
    schema_path = Path(__file__).parent / "db_schema.sql"
    with open(schema_path) as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


def populate_genres(conn):
    world_path = Path(__file__).parent.parent / "web" / "public" / "data" / "world.json"
    with open(world_path) as f:
        world = json.load(f)
    for genre in world.get("genres", []):
        conn.execute(
            "INSERT OR REPLACE INTO genres (name, slug, scene, biome, year, description) VALUES (?, ?, ?, ?, ?, ?)",
            (genre["name"], genre["slug"], genre.get("scene"), genre.get("biome"),
             genre.get("year"), genre.get("description", "")[:500])
        )
    for link in world.get("links", []):
        conn.execute(
            "INSERT OR IGNORE INTO genre_links (source_id, target_id, link_type) "
            "SELECT g1.id, g2.id, 'influence' FROM genres g1, genres g2 "
            "WHERE g1.slug = ? AND g2.slug = ?",
            (link["source"], link["target"])
        )
    conn.commit()
    print(f"Loaded {len(world['genres'])} genres, {len(world['links'])} links")


def populate_taxonomy(conn):
    from taxonomy_bridge import build_bridge
    bridge = build_bridge()
    for style, genres in bridge["style_to_genres"].items():
        for genre in genres:
            conn.execute(
                "INSERT OR IGNORE INTO taxonomy_bridge (discogs_style, genre_id, confidence) "
                "SELECT ?, id, 1.0 FROM genres WHERE name = ?",
                (style, genre)
            )
    conn.commit()
    print(f"Loaded taxonomy bridge: {len(bridge['style_to_genres'])} styles mapped")


def populate_cooccurrence(conn):
    from style_cooccurrence import build_cooccurrence, load_releases
    matrix = build_cooccurrence()
    top_pairs = sorted(matrix.items(), key=lambda x: -x[1])[:2000]
    for (a, b), count in top_pairs:
        conn.execute(
            "INSERT OR REPLACE INTO style_cooccurrence VALUES (?, ?, ?)",
            (a, b, count)
        )
    conn.commit()
    print(f"Loaded {len(top_pairs)} style co-occurrence pairs")


def populate_releases(conn, sample_size=None):
    from style_cooccurrence import load_releases
    releases = load_releases()
    if sample_size:
        releases = islice(releases, sample_size)
    batch = []
    for i, r in enumerate(releases):
        videos = r.get("videos", [])
        youtube = next((v["uri"] for v in videos if "youtube" in v.get("uri", "")), None)
        batch.append((
            r.get("id"), r.get("title", ""), r.get("artists", [{}])[0].get("name", ""),
            r.get("labels", [{}])[0].get("name", ""), r.get("labels", [{}])[0].get("catno", ""),
            r.get("country", ""), r.get("year", 0),
            r.get("formats", [{}])[0].get("name", ""),
            json.dumps(r.get("styles", [])), youtube
        ))
        if len(batch) >= 10000:
            conn.executemany(
                "INSERT OR IGNORE INTO releases (discogs_id, title, artist, label, catno, country, year, format, styles, youtube_url) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", batch
            )
            conn.commit()
            batch = []
            if (i + 1) % 100000 == 0:
                print(f"  ... {i + 1:,} releases loaded")
    if batch:
        conn.executemany(
            "INSERT OR IGNORE INTO releases (discogs_id, title, artist, label, catno, country, year, format, styles, youtube_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", batch
        )
        conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
    print(f"Loaded {total:,} releases")


def main():
    parser = argparse.ArgumentParser(description="Build DiscoWorld unified database")
    parser.add_argument("--sample", type=int, help="Limit releases to N for testing")
    parser.add_argument("--skip-similarity", action="store_true", help="Skip similarity index (slow)")
    args = parser.parse_args()

    print(f"Building DiscoWorld database at {DB_PATH}")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = create_db()
    populate_genres(conn)
    populate_taxonomy(conn)
    populate_cooccurrence(conn)
    populate_releases(conn, sample_size=args.sample)

    if not args.skip_similarity:
        print("Building similarity index... (this may take a while)")
        from similarity_index import build_and_store_neighbors
        build_and_store_neighbors(conn)

    conn.close()
    size_mb = DB_PATH.stat().st_size / 1024 / 1024
    print(f"Done! Database: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Test with sample data**

```bash
cd /Users/yoyaku/repos/discoworld/packages/pipeline
python3 build_db.py --sample 1000 --skip-similarity
```

Expected: Database created with genres, taxonomy, co-occurrence, and 1000 releases

- [ ] **Step 4: Verify database**

```bash
cd /Users/yoyaku/repos/discoworld
python3 -c "
import sqlite3
conn = sqlite3.connect('data/discoworld.db')
for table in ['genres', 'genre_links', 'taxonomy_bridge', 'style_cooccurrence', 'releases']:
    count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f'{table}: {count}')
conn.close()
"
```

- [ ] **Step 5: Commit**

```bash
git add packages/pipeline/db_schema.sql packages/pipeline/build_db.py
git commit -m "feat: unified SQLite database builder — genres, taxonomy, releases"
```

---

## Chunk 2: Similarity Index + API

### Task 6: Content-based similarity index

**Files:**
- Create: `packages/pipeline/similarity_index.py`
- Create: `packages/pipeline/tests/test_similarity.py`

- [ ] **Step 1: Write failing test**

```python
# packages/pipeline/tests/test_similarity.py
import pytest
from similarity_index import build_feature_vectors, find_neighbors

def test_same_style_releases_are_similar():
    releases = [
        {"id": 1, "styles": ["Deep House", "House"], "label": "Trax", "year": 1990},
        {"id": 2, "styles": ["Deep House", "House"], "label": "Trax", "year": 1991},
        {"id": 3, "styles": ["Gabber", "Hardcore"], "label": "Mokum", "year": 1995},
    ]
    vectors = build_feature_vectors(releases)
    neighbors = find_neighbors(vectors, release_id=1, top_n=2)
    assert neighbors[0][0] == 2  # Release 2 should be most similar to 1

def test_different_styles_low_similarity():
    releases = [
        {"id": 1, "styles": ["Deep House"], "label": "A", "year": 1990},
        {"id": 2, "styles": ["Gabber"], "label": "B", "year": 1995},
    ]
    vectors = build_feature_vectors(releases)
    neighbors = find_neighbors(vectors, release_id=1, top_n=1)
    assert neighbors[0][1] < 0.5  # Low similarity score
```

- [ ] **Step 2: Run test — verify fail**

```bash
cd /Users/yoyaku/repos/discoworld/packages/pipeline
python3 -m pytest tests/test_similarity.py -v
```

- [ ] **Step 3: Write implementation**

```python
# packages/pipeline/similarity_index.py
"""
Content-based similarity index for vinyl releases.
Feature vector: style_ids (binary) + label overlap + year proximity.
Uses sparse matrix + cosine similarity from scikit-learn.
"""
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


def build_feature_vectors(releases: list[dict], all_styles: list[str] | None = None):
    if all_styles is None:
        all_styles = sorted(set(s for r in releases for s in r.get("styles", [])))
    style_idx = {s: i for i, s in enumerate(all_styles)}

    all_labels = sorted(set(r.get("label", "") for r in releases))
    label_idx = {l: i + len(all_styles) for i, l in enumerate(all_labels)}

    n_features = len(all_styles) + len(all_labels)
    rows, cols, data = [], [], []
    id_to_row = {}

    for row_i, release in enumerate(releases):
        rid = release.get("id", row_i)
        id_to_row[rid] = row_i
        for style in release.get("styles", []):
            if style in style_idx:
                rows.append(row_i)
                cols.append(style_idx[style])
                data.append(1.0)
        label = release.get("label", "")
        if label in label_idx:
            rows.append(row_i)
            cols.append(label_idx[label])
            data.append(0.5)  # Label weight lower than style

    matrix = csr_matrix((data, (rows, cols)), shape=(len(releases), n_features))
    return {"matrix": matrix, "id_to_row": id_to_row, "row_to_id": {v: k for k, v in id_to_row.items()}}


def find_neighbors(vectors: dict, release_id: int, top_n: int = 10) -> list[tuple[int, float]]:
    row = vectors["id_to_row"].get(release_id)
    if row is None:
        return []
    query = vectors["matrix"][row]
    similarities = cosine_similarity(query, vectors["matrix"]).flatten()
    # Exclude self
    similarities[row] = -1
    top_indices = np.argsort(similarities)[-top_n:][::-1]
    return [(vectors["row_to_id"][i], float(similarities[i])) for i in top_indices if similarities[i] > 0]


def build_and_store_neighbors(conn: sqlite3.Connection, top_n: int = 50, vinyl_only: bool = True):
    query = "SELECT id, styles, label, year FROM releases"
    if vinyl_only:
        query += " WHERE format = 'Vinyl'"
    cursor = conn.execute(query)
    releases = []
    for row in cursor:
        releases.append({
            "id": row[0],
            "styles": json.loads(row[1]) if row[1] else [],
            "label": row[2] or "",
            "year": row[3] or 0,
        })

    if not releases:
        print("No releases found for similarity index")
        return

    print(f"Building similarity index for {len(releases):,} releases...")
    vectors = build_feature_vectors(releases)

    batch = []
    for i, release in enumerate(releases):
        neighbors = find_neighbors(vectors, release["id"], top_n=top_n)
        for neighbor_id, score in neighbors:
            batch.append((release["id"], neighbor_id, round(score, 4)))
        if len(batch) >= 10000:
            conn.executemany(
                "INSERT OR REPLACE INTO release_neighbors VALUES (?, ?, ?)", batch
            )
            conn.commit()
            batch = []
        if (i + 1) % 1000 == 0:
            print(f"  ... {i + 1:,}/{len(releases):,} releases indexed")

    if batch:
        conn.executemany(
            "INSERT OR REPLACE INTO release_neighbors VALUES (?, ?, ?)", batch
        )
        conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM release_neighbors").fetchone()[0]
    print(f"Similarity index complete: {total:,} neighbor pairs")
```

- [ ] **Step 4: Run tests**

```bash
pip install scikit-learn scipy  # if not installed
cd /Users/yoyaku/repos/discoworld/packages/pipeline
python3 -m pytest tests/test_similarity.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add packages/pipeline/similarity_index.py packages/pipeline/tests/test_similarity.py
git commit -m "feat: content-based similarity index — cosine distance on style+label vectors"
```

### Task 7: FastAPI recommendation endpoint

**Files:**
- Create: `packages/api/db.py`
- Create: `packages/api/routes/recommendations.py`
- Create: `packages/api/routes/releases.py`
- Modify: `packages/api/main.py`

- [ ] **Step 1: Write DB helper**

```python
# packages/api/db.py
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATHS = [
    Path(__file__).parent.parent.parent / "data" / "discoworld.db",
    Path("/var/www/world.yoyaku.io/data/discoworld.db"),
]

def get_db_path() -> Path:
    for path in DB_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError("DiscoWorld database not found")

@contextmanager
def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

- [ ] **Step 2: Write recommendations route**

```python
# packages/api/routes/recommendations.py
from fastapi import APIRouter, HTTPException, Query
from db import get_db

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

@router.get("/{release_id}")
def get_recommendations(release_id: int, limit: int = Query(10, le=50)):
    with get_db() as conn:
        release = conn.execute(
            "SELECT * FROM releases WHERE id = ? OR discogs_id = ?",
            (release_id, release_id)
        ).fetchone()
        if not release:
            raise HTTPException(404, "Release not found")

        neighbors = conn.execute(
            "SELECT r.*, rn.score FROM release_neighbors rn "
            "JOIN releases r ON r.id = rn.neighbor_id "
            "WHERE rn.release_id = ? ORDER BY rn.score DESC LIMIT ?",
            (release["id"], limit)
        ).fetchall()

        return {
            "release": dict(release),
            "recommendations": [dict(n) for n in neighbors],
        }
```

- [ ] **Step 3: Write releases route**

```python
# packages/api/routes/releases.py
from fastapi import APIRouter, Query
from db import get_db

router = APIRouter(prefix="/api/releases", tags=["releases"])

@router.get("")
def search_releases(
    genre: str | None = None,
    style: str | None = None,
    country: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    label: str | None = None,
    q: str | None = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0),
):
    with get_db() as conn:
        conditions = []
        params = []

        if style:
            conditions.append("styles LIKE ?")
            params.append(f'%"{style}"%')
        if country:
            conditions.append("country = ?")
            params.append(country)
        if year_min:
            conditions.append("year >= ?")
            params.append(year_min)
        if year_max:
            conditions.append("year <= ?")
            params.append(year_max)
        if label:
            conditions.append("label LIKE ?")
            params.append(f"%{label}%")
        if q:
            conditions.append("(title LIKE ? OR artist LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM releases WHERE {where} ORDER BY year DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        releases = conn.execute(query, params).fetchall()
        total = conn.execute(f"SELECT COUNT(*) FROM releases WHERE {where}", params[:-2]).fetchone()[0]

        return {"releases": [dict(r) for r in releases], "total": total}
```

- [ ] **Step 4: Wire routes into main.py**

Add to `packages/api/main.py`:

```python
from routes.recommendations import router as recommendations_router
from routes.releases import router as releases_router

app.include_router(recommendations_router)
app.include_router(releases_router)
```

- [ ] **Step 5: Test API locally**

```bash
cd /Users/yoyaku/repos/discoworld/packages/api
uvicorn main:app --reload --port 8200 &
sleep 2
curl http://localhost:8200/api/releases?style=Techno&limit=3 | python3 -m json.tool
curl http://localhost:8200/api/health
kill %1
```

- [ ] **Step 6: Commit**

```bash
git add packages/api/db.py packages/api/routes/ packages/api/main.py
git commit -m "feat: API endpoints — /recommendations/{id} + /releases with filters"
```

### Task 8: Full pipeline run

- [ ] **Step 1: Build full database (sample 50K for speed)**

```bash
cd /Users/yoyaku/repos/discoworld/packages/pipeline
python3 build_db.py --sample 50000
```

Expected: Database with genres, taxonomy bridge, co-occurrence, 50K releases

- [ ] **Step 2: Build similarity index on sample**

```bash
python3 build_db.py --sample 10000
```

Expected: Similarity index built for vinyl releases in sample

- [ ] **Step 3: Test full API flow**

```bash
cd /Users/yoyaku/repos/discoworld/packages/api
uvicorn main:app --port 8200 &
sleep 2
# Get a release ID
RELEASE_ID=$(curl -s http://localhost:8200/api/releases?limit=1 | python3 -c "import sys,json; print(json.load(sys.stdin)['releases'][0]['id'])")
# Get recommendations
curl -s "http://localhost:8200/api/recommendations/$RELEASE_ID" | python3 -m json.tool
kill %1
```

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: Phase 0 complete — unified data foundation with taxonomy, similarity, API"
git push
```
