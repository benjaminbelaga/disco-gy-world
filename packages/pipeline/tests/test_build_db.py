"""Tests for the build_db orchestrator — schema creation and populate functions."""
import sys
import json
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from build_db import create_db, populate_genres


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary database with schema applied."""
    db_path = tmp_path / "test.db"
    conn = create_db(db_path)
    yield conn, db_path
    conn.close()


def test_create_db_creates_file(tmp_path):
    db_path = tmp_path / "test.db"
    conn = create_db(db_path)
    conn.close()
    assert db_path.exists()


def test_create_db_creates_genres_table(tmp_db):
    conn, _ = tmp_db
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='genres'"
    ).fetchall()
    assert len(tables) == 1


def test_create_db_creates_releases_table(tmp_db):
    conn, _ = tmp_db
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='releases'"
    ).fetchall()
    assert len(tables) == 1


def test_create_db_creates_all_expected_tables(tmp_db):
    conn, _ = tmp_db
    expected = {
        "genres", "genre_links", "taxonomy_bridge",
        "style_cooccurrence", "releases", "release_neighbors",
        "users", "user_collection",
    }
    tables = {
        row[0] for row in
        conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"


def test_create_db_creates_indexes(tmp_db):
    conn, _ = tmp_db
    indexes = {
        row[0] for row in
        conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    }
    assert "idx_releases_year" in indexes
    assert "idx_releases_country" in indexes


def test_create_db_is_idempotent(tmp_path):
    """Running create_db twice on the same path should not error."""
    db_path = tmp_path / "test.db"
    conn1 = create_db(db_path)
    conn1.execute("INSERT INTO genres (name, slug) VALUES ('Test', 'test')")
    conn1.commit()
    conn1.close()

    conn2 = create_db(db_path)
    count = conn2.execute("SELECT COUNT(*) FROM genres").fetchone()[0]
    conn2.close()
    # IF NOT EXISTS means tables aren't recreated, data persists
    assert count == 1


def test_genres_table_columns(tmp_db):
    conn, _ = tmp_db
    cursor = conn.execute("PRAGMA table_info(genres)")
    columns = {row[1] for row in cursor.fetchall()}
    expected = {"id", "name", "slug", "scene", "biome", "bpm_min", "bpm_max",
                "emerged", "year", "release_count", "description"}
    assert expected == columns


def test_releases_table_columns(tmp_db):
    conn, _ = tmp_db
    cursor = conn.execute("PRAGMA table_info(releases)")
    columns = {row[1] for row in cursor.fetchall()}
    expected = {"id", "discogs_id", "title", "artist", "label", "catno",
                "country", "year", "format", "styles", "youtube_url"}
    assert expected == columns


def test_populate_genres_with_world_json(tmp_db):
    """Test populate_genres loads real world.json data."""
    conn, _ = tmp_db
    world_path = Path(__file__).parent.parent.parent / "web" / "public" / "data" / "world.json"
    if not world_path.exists():
        pytest.skip("world.json not available")

    populate_genres(conn)
    count = conn.execute("SELECT COUNT(*) FROM genres").fetchone()[0]
    assert count > 100, f"Expected 100+ genres, got {count}"


def test_manual_genre_insert(tmp_db):
    """Test manual insert into genres table respects schema."""
    conn, _ = tmp_db
    conn.execute(
        "INSERT INTO genres (name, slug, scene, biome, year) VALUES (?, ?, ?, ?, ?)",
        ("Minimal Techno", "minimal-techno", "Techno", "techno-massif", 1994),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM genres WHERE slug='minimal-techno'").fetchone()
    assert row is not None
    assert row[1] == "Minimal Techno"


def test_genre_links_foreign_key(tmp_db):
    """Test genre_links references genres correctly."""
    conn, _ = tmp_db
    conn.execute("INSERT INTO genres (name, slug) VALUES ('A', 'a')")
    conn.execute("INSERT INTO genres (name, slug) VALUES ('B', 'b')")
    conn.commit()

    id_a = conn.execute("SELECT id FROM genres WHERE slug='a'").fetchone()[0]
    id_b = conn.execute("SELECT id FROM genres WHERE slug='b'").fetchone()[0]

    conn.execute(
        "INSERT INTO genre_links (source_id, target_id, link_type) VALUES (?, ?, 'influence')",
        (id_a, id_b),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM genre_links").fetchone()
    assert row[0] == id_a
    assert row[1] == id_b
