-- DiscoWorld unified database schema

CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    scene TEXT,
    biome TEXT,
    year INTEGER,
    description TEXT
);

CREATE TABLE IF NOT EXISTS genre_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES genres(id),
    target_id INTEGER NOT NULL REFERENCES genres(id),
    link_type TEXT NOT NULL DEFAULT 'influence',
    UNIQUE(source_id, target_id)
);

CREATE TABLE IF NOT EXISTS taxonomy_bridge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discogs_style TEXT NOT NULL,
    genre_id INTEGER NOT NULL REFERENCES genres(id),
    confidence REAL NOT NULL DEFAULT 1.0,
    UNIQUE(discogs_style, genre_id)
);

CREATE TABLE IF NOT EXISTS style_cooccurrence (
    style_a TEXT NOT NULL,
    style_b TEXT NOT NULL,
    count INTEGER NOT NULL,
    PRIMARY KEY (style_a, style_b)
);

-- `sku` and `shop_url` are the YOYAKU join: present when we carry the record,
-- NULL otherwise, so "do we have it" is a column rather than a network call.
--
-- The alternative was a live /api/carried layer calling by-discogs per release,
-- with its own cache, TTLs and a 120 req/min/IP budget to respect. It was
-- dropped once the overlap was measured: only 618 of the shop's 10,236
-- discogs-identified products existed in the corpus, so the badge would have
-- lit on 0.06% of releases — an expensive lookup for a feature nobody sees.
-- Carrying the shop as a corpus source fixes the sparsity at its root instead.
--
-- Price and stock deliberately stay out. They change hourly and would be stale
-- the moment they were written; `shop_url` leads to the page that owns them.
CREATE TABLE IF NOT EXISTS releases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discogs_id INTEGER UNIQUE,
    title TEXT NOT NULL,
    artist TEXT,
    label TEXT,
    catno TEXT,
    country TEXT,
    year INTEGER,
    format TEXT,
    styles TEXT,
    youtube_url TEXT,
    sku TEXT,
    shop_url TEXT
);
CREATE INDEX IF NOT EXISTS idx_releases_shop_url ON releases(shop_url) WHERE shop_url IS NOT NULL;

-- `score` is a SIMILARITY (higher is closer), not a distance. It was declared
-- as `distance` while similarity_index.py wrote find_neighbors()' score into it
-- positionally and recommendations.py read it back as `rn.score` — so the
-- producer worked, the consumer raised "no such column: rn.score", and nobody
-- saw it because the table never existed on a deployed host. Renamed rather
-- than aliased: a column called `distance` that must be sorted DESC is a trap
-- that inverts recommendations the first time someone writes the obvious ASC.
CREATE TABLE IF NOT EXISTS release_neighbors (
    release_id INTEGER NOT NULL,
    neighbor_id INTEGER NOT NULL,
    score REAL NOT NULL,
    PRIMARY KEY (release_id, neighbor_id)
);

CREATE INDEX IF NOT EXISTS idx_genres_slug ON genres(slug);
CREATE INDEX IF NOT EXISTS idx_releases_year ON releases(year);
CREATE INDEX IF NOT EXISTS idx_releases_artist ON releases(artist);
CREATE INDEX IF NOT EXISTS idx_releases_label ON releases(label);
CREATE INDEX IF NOT EXISTS idx_taxonomy_style ON taxonomy_bridge(discogs_style);
