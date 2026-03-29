# Contributing to DiscoWorld

Welcome! DiscoWorld is a community-driven project to map all electronic music into an explorable 3D world. Whether you know music, code, or data — there's a way to help.

---

## Five Ways to Contribute

### 1. Genre Cartographers
Refine genre boundaries, add missing sub-genres, describe genre characteristics, and fix connection links between genres.

### 2. City Scouts
Add cities and their musical scenes to Earth Mode. Document local genres, key labels, and the time periods when scenes were active.

### 3. Crate Curators
Suggest tracks that define a genre neighborhood. These become the "landmark" releases that help orient explorers.

### 4. Data Enrichers
Improve release metadata, fix genre classifications, and help bridge the gap between Discogs styles and our taxonomy.

### 5. Visual Builders
Build UI components, write shaders, improve 3D performance, design biome aesthetics, or create new visualizations.

---

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- Git

### Development Setup

```bash
# Clone the repo
git clone https://github.com/discoworld/discoworld.git
cd discoworld

# Frontend
cd packages/web
npm install
npm run dev
# → http://localhost:5173

# API (in another terminal)
cd packages/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Data pipeline (optional — only if you need to rebuild the DB)
cd packages/pipeline
pip install -r requirements.txt
python build_db.py
```

### Running Tests

```bash
# All tests (from repo root)
cd ~/repos/discoworld

# API tests (87 tests)
python3 -m pytest packages/api/tests/ -v

# Pipeline tests (63+ tests)
python3 -m pytest packages/pipeline/tests/ -v

# Frontend unit tests (137+ tests)
cd packages/web && npx vitest run

# Playwright E2E tests (43+ tests)
cd packages/web && npx playwright test

# Frontend lint
cd packages/web && npm run lint
```

### Code Architecture

```
packages/
├── api/          FastAPI Python backend
│   ├── main.py           App entry + inline endpoints (/genres, /search, /stats)
│   ├── db.py             SQLite connection helper (discoworld.db)
│   ├── user_db.py        User SQLite (discoworld_users.db)
│   ├── discogs_client.py Discogs API client (rate-limited)
│   └── routes/           16 API routers
│       ├── releases.py       Release search + community stats
│       ├── recommendations.py Content-based neighbors
│       ├── search.py         Fuzzy unified search (genres, artists, labels)
│       ├── auth.py           Discogs OAuth 1.0a + token fallback
│       ├── collection.py     User collection sync + browse
│       ├── genre_edits.py    Community genre editing + voting
│       ├── contributors.py   Contributor leaderboard + profiles
│       └── ...               artists, cities, labels, shops, paths, taste_profile
├── web/          React + Three.js frontend
│   ├── src/
│   │   ├── App.jsx           Main app (3 views, progressive disclosure)
│   │   ├── stores/           Zustand stores (main + audio)
│   │   ├── components/       40+ React components
│   │   ├── lib/              Core libraries
│   │   │   ├── plugins/          RecordStoreAdapter plugin system
│   │   │   ├── strudelPatterns.js Genre→music pattern generator
│   │   │   ├── soundscape.js     Procedural biome ambient audio
│   │   │   ├── shareCard.js      OG image generator
│   │   │   ├── buildingSystem.js Procedural genre architecture
│   │   │   └── driftEngine.js    Serendipity auto-navigation
│   │   └── __tests__/        11 test files
│   └── e2e/              Playwright browser tests
└── pipeline/     Python data processing
    ├── build_db.py           Orchestrator (JSONL → SQLite)
    ├── taxonomy_bridge.py    Discogs ↔ Ishkur mapping
    ├── similarity_index.py   Content-based neighbors
    ├── extract_label_locations.py  30K labels from dump
    ├── musicbrainz_crossref.py     MusicBrainz enrichment
    └── ...                   15+ pipeline scripts
```

---

## Submitting Changes

### Code Contributions

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Run linting and tests
4. Open a Pull Request with a clear description of what changed and why

### Data Contributions

For genre edits, city additions, and taxonomy changes, use GitHub Issues with the appropriate template:

**Genre correction format:**
```yaml
Genre: [name]
Current state: [what's wrong]
Proposed change: [your fix]
Source: [Ishkur / RA / Wikipedia / Discogs / other]
```

**City addition format:**
```yaml
City: [name]
Country: [code]
Coordinates: [lat, lng]
Genres: [genres associated with this city]
Active period: [decade range]
Key labels: [notable labels from this city]
Source: [reference URL]
```

**Track suggestion format:**
```yaml
Genre: [target genre/neighborhood]
Artist: [name]
Title: [name]
Label: [name]
Year: [year]
Discogs URL: [link]
Why: [why this track defines this neighborhood]
```

---

## Code Style

### JavaScript / React
- ESLint config is in `packages/web/eslint.config.js` — run `npm run lint`
- Functional components with hooks
- Zustand for state management
- Descriptive variable names, no abbreviations

### Python
- Format with [black](https://github.com/psf/black): `black .`
- Type hints on all function signatures
- Docstrings on public functions

---

## Genre Dispute Resolution

Genre boundaries are inherently subjective. When there's disagreement:

1. **Cite sources.** Acceptable references: [Ishkur's Guide](https://music.ishkur.com/), [Resident Advisor](https://ra.co/), Wikipedia, [Discogs](https://www.discogs.com/) style tags, academic papers.
2. **Discuss in the Issue.** Keep it respectful. Multiple perspectives are valuable.
3. **Maintainers decide** when consensus can't be reached, with reasoning documented in the Issue.

The goal is accuracy and usefulness, not gatekeeping.

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you agree to uphold a welcoming, inclusive environment.

**In short:** be respectful, be constructive, assume good intent.

---

## Questions?

Open a [Discussion](https://github.com/discoworld/discoworld/discussions) or file an Issue. We're happy to help you get started.
