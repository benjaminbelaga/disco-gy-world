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

-- User auth & collection (separate DB: discoworld_users.db)
-- Included here for reference; actual creation handled by user_db.py

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    discogs_username TEXT UNIQUE,
    access_token TEXT,
    access_secret TEXT,
    avatar_url TEXT,
    synced_at DATETIME
);

CREATE TABLE IF NOT EXISTS user_collection (
    user_id INTEGER REFERENCES users(id),
    release_id INTEGER,
    discogs_release_id INTEGER,
    rating INTEGER,
    date_added DATETIME,
    source TEXT DEFAULT 'collection',
    PRIMARY KEY (user_id, discogs_release_id)
);

CREATE INDEX IF NOT EXISTS idx_releases_year ON releases(year);
CREATE INDEX IF NOT EXISTS idx_releases_country ON releases(country);
CREATE INDEX IF NOT EXISTS idx_releases_label ON releases(label);
CREATE INDEX IF NOT EXISTS idx_release_neighbors_score ON release_neighbors(score DESC);
CREATE INDEX IF NOT EXISTS idx_releases_discogs_id ON releases(discogs_id);
CREATE INDEX IF NOT EXISTS idx_user_collection_user ON user_collection(user_id);
CREATE INDEX IF NOT EXISTS idx_user_collection_source ON user_collection(user_id, source);
CREATE INDEX IF NOT EXISTS idx_releases_artist ON releases(artist);
