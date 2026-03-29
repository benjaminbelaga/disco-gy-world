"""User database — SQLite tables for auth, collection, wantlist."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

# User DB lives alongside the main data DB
_USER_DB_PATHS = [
    Path(__file__).resolve().parent.parent.parent / "data" / "discoworld_users.db",
    Path("/var/www/world.yoyaku.io/data/discoworld_users.db"),
]

_SCHEMA = """
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

CREATE INDEX IF NOT EXISTS idx_user_collection_user ON user_collection(user_id);
CREATE INDEX IF NOT EXISTS idx_user_collection_source ON user_collection(user_id, source);
"""


def _get_user_db_path() -> Path:
    """Return the first writable DB path, creating the file if needed."""
    for path in _USER_DB_PATHS:
        if path.parent.exists():
            return path
    # Fallback: create in the first candidate's parent
    _USER_DB_PATHS[0].parent.mkdir(parents=True, exist_ok=True)
    return _USER_DB_PATHS[0]


def init_user_db() -> None:
    """Create user tables if they don't exist."""
    db_path = _get_user_db_path()
    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA)
    conn.close()


@contextmanager
def get_user_db():
    """Context manager for user SQLite connections."""
    db_path = _get_user_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()
