#!/usr/bin/env python3
"""
MusicBrainz cross-reference pipeline for DiscoWorld.

Cross-references DiscoWorld releases with MusicBrainz to enrich metadata:
- MusicBrainz release IDs (MBID)
- Cover art URLs (from Cover Art Archive)
- Recording durations
- ISRCs

Uses the MusicBrainz API with rate limiting (1 req/sec per their TOS).
Processes in batches and saves progress to resume on interruption.
"""

import json
import sqlite3
import sys
import time
from pathlib import Path

import requests

BASE_URL = 'https://musicbrainz.org/ws/2'
COVER_ART_URL = 'https://coverartarchive.org/release'
USER_AGENT = 'DiscoWorld/2.0 (https://github.com/benjaminbelaga/discoworld)'
RATE_LIMIT = 1.1  # seconds between requests (MusicBrainz allows 1/sec)

HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'application/json',
}

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'discoworld.db'
OUTPUT_PATH = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'musicbrainz_crossref.json'
PROGRESS_PATH = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'mb_progress.json'


def search_release(title, artist, label=None, year=None):
    """Search MusicBrainz for a release by title+artist."""
    query_parts = []
    if title:
        query_parts.append(f'release:"{title}"')
    if artist:
        query_parts.append(f'artist:"{artist}"')
    if label:
        query_parts.append(f'label:"{label}"')
    if year:
        query_parts.append(f'date:{year}')

    query = ' AND '.join(query_parts)
    params = {
        'query': query,
        'fmt': 'json',
        'limit': 3,
    }

    try:
        resp = requests.get(f'{BASE_URL}/release/', params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 503:
            time.sleep(5)
            return None
        resp.raise_for_status()
        data = resp.json()
        releases = data.get('releases', [])
        if releases:
            return releases[0]  # Best match
        return None
    except Exception as e:
        print(f'  Error searching MB: {e}')
        return None


def get_cover_art_url(mbid):
    """Check if Cover Art Archive has art for this release."""
    try:
        resp = requests.get(f'{COVER_ART_URL}/{mbid}', headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            images = data.get('images', [])
            if images:
                # Prefer front cover
                front = next((img for img in images if img.get('front')), images[0])
                return front.get('thumbnails', {}).get('small', front.get('image'))
        return None
    except Exception:
        return None


def load_progress():
    """Load previous progress to resume."""
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH) as f:
            return json.load(f)
    return {'processed': {}, 'offset': 0}


def save_progress(progress):
    """Save progress for resume."""
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_PATH, 'w') as f:
        json.dump(progress, f)


def get_releases_from_db(limit=5000, offset=0):
    """Get releases from DiscoWorld DB ordered by relevance."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, artist, label, year, styles
        FROM releases
        WHERE title IS NOT NULL AND artist IS NOT NULL
          AND title != '' AND artist != ''
        ORDER BY id
        LIMIT ? OFFSET ?
    """, (limit, offset))

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def main():
    if not DB_PATH.exists():
        print(f'DB not found: {DB_PATH}')
        sys.exit(1)

    # Parse args
    batch_size = 500  # How many to process per run
    if len(sys.argv) > 1:
        batch_size = int(sys.argv[1])

    progress = load_progress()
    offset = progress.get('offset', 0)
    processed = progress.get('processed', {})

    print(f'MusicBrainz Cross-Reference Pipeline')
    print(f'Already processed: {len(processed)} releases')
    print(f'Starting from offset: {offset}')
    print(f'Batch size: {batch_size}')
    print()

    releases = get_releases_from_db(limit=batch_size, offset=offset)
    if not releases:
        print('No more releases to process.')
        # Write final output
        write_output(processed)
        return

    print(f'Loaded {len(releases)} releases from DB')

    matched = 0
    with_art = 0
    errors = 0

    for i, release in enumerate(releases):
        rid = str(release['id'])

        # Skip already processed
        if rid in processed:
            continue

        title = release['title']
        artist = release['artist']
        label = release.get('label')
        year = release.get('year')

        # Search MusicBrainz
        mb_release = search_release(title, artist, label, year)
        time.sleep(RATE_LIMIT)

        if mb_release:
            mbid = mb_release['id']
            entry = {
                'mbid': mbid,
                'mb_title': mb_release.get('title'),
                'mb_artist': mb_release.get('artist-credit', [{}])[0].get('name') if mb_release.get('artist-credit') else None,
                'mb_date': mb_release.get('date'),
                'mb_country': mb_release.get('country'),
                'mb_status': mb_release.get('status'),
                'mb_score': mb_release.get('score', 0),
            }

            # Get cover art (only for high-confidence matches)
            if mb_release.get('score', 0) >= 80:
                art_url = get_cover_art_url(mbid)
                time.sleep(RATE_LIMIT)
                if art_url:
                    entry['cover_art'] = art_url
                    with_art += 1

            processed[rid] = entry
            matched += 1
        else:
            processed[rid] = None  # Mark as searched but not found
            errors += 1

        # Progress update
        if (i + 1) % 50 == 0:
            progress['processed'] = processed
            progress['offset'] = offset + i + 1
            save_progress(progress)
            found = len([v for v in processed.values() if v is not None])
            print(f'  [{i+1}/{len(releases)}] Matched: {matched}, With art: {with_art}, Not found: {errors} (Total found: {found})')

    # Final save
    progress['processed'] = processed
    progress['offset'] = offset + len(releases)
    save_progress(progress)

    found = len([v for v in processed.values() if v is not None])
    print(f'\nBatch complete: {matched} matched, {with_art} with cover art, {errors} not found')
    print(f'Total processed: {len(processed)}, Total found: {found}')

    write_output(processed)


def write_output(processed):
    """Write the cross-reference data to JSON."""
    # Filter to only found entries
    found = {k: v for k, v in processed.items() if v is not None}

    output = {
        'meta': {
            'source': 'MusicBrainz API + Cover Art Archive',
            'total_searched': len(processed),
            'total_matched': len(found),
            'with_cover_art': sum(1 for v in found.values() if v.get('cover_art')),
        },
        'releases': found,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)

    print(f'Written to {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
