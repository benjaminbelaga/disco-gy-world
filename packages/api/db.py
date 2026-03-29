"""SQLite connection helper for DiscoWorld API."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATHS = [
    Path(__file__).resolve().parent.parent.parent / "data" / "discoworld.db",
    Path("/var/www/world.yoyaku.io/data/discoworld.db"),
]


def get_db_path() -> Path | None:
    """Return the first existing database path, or None."""
    for path in DB_PATHS:
        if path.exists():
            return path
    return None


@contextmanager
def get_db():
    """Context manager for SQLite connections. Raises FileNotFoundError if no DB."""
    db_path = get_db_path()
    if db_path is None:
        raise FileNotFoundError(
            "DiscoWorld database not found. Run build_db.py first."
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def db_available() -> bool:
    """Check if the database file exists."""
    return get_db_path() is not None
