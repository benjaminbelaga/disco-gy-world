#!/usr/bin/env python3
"""
Enrich DiscoWorld releases with Discogs community stats (have/want counts).

Uses the Discogs API to fetch community data for releases.
Rate limit: 60 requests/minute (unauthenticated) or 240/min (authenticated).

Usage:
  python3 enrich_community_stats.py [batch_size] [--token DISCOGS_TOKEN]

Without a token, rate limit is 25 requests/minute to be safe.
With a token, rate limit is 60 requests/minute.
"""

import json
import sqlite3
import sys
import time
from pathlib import Path

import requests

BASE_URL = 'https://api.discogs.com'
USER_AGENT = 'DiscoWorld/2.0 +https://github.com/benjaminbelaga/discoworld'

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'discoworld.db'
OUTPUT_PATH = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'community_stats.json'
PROGRESS_PATH = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'community_progress.json'


def get_release_stats(discogs_id, token=None):
    """Fetch community stats for a release from Discogs API."""
    headers = {'User-Agent': USER_AGENT}
    if token:
        headers['Authorization'] = f'Discogs token={token}'

    try:
        resp = requests.get(
            f'{BASE_URL}/releases/{discogs_id}',
            headers=headers,
            timeout=15,
            params={'curr_abbr': 'USD'},
        )
        if resp.status_code == 429:
            # Rate limited — wait and retry
            retry_after = int(resp.headers.get('Retry-After', 60))
            print(f'  Rate limited, waiting {retry_after}s...')
            time.sleep(retry_after)
            return get_release_stats(discogs_id, token)

        if resp.status_code == 404:
            return None

        resp.raise_for_status()
        data = resp.json()

        community = data.get('community', {})
        return {
            'have': community.get('have', 0),
            'want': community.get('want', 0),
            'rating_average': community.get('rating', {}).get('average', 0),
            'rating_count': community.get('rating', {}).get('count', 0),
            'num_for_sale': data.get('num_for_sale', 0),
            'lowest_price': data.get('lowest_price'),
        }
    except requests.exceptions.RequestException as e:
        print(f'  Error fetching {discogs_id}: {e}')
        return None


def load_progress():
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH) as f:
            return json.load(f)
    return {'stats': {}, 'offset': 0}


def save_progress(progress):
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_PATH, 'w') as f:
        json.dump(progress, f)


def get_releases_with_discogs_id(limit=500, offset=0):
    """Get releases that have a Discogs ID for API lookup."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, discogs_id, title, artist
        FROM releases
        WHERE discogs_id IS NOT NULL AND discogs_id > 0
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
    batch_size = 200
    token = None
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == '--token' and i + 1 < len(args):
            token = args[i + 1]
        elif arg.isdigit():
            batch_size = int(arg)

    rate_delay = 2.5 if not token else 1.0  # seconds between requests

    progress = load_progress()
    offset = progress.get('offset', 0)
    stats = progress.get('stats', {})

    print(f'Discogs Community Stats Enrichment')
    print(f'Auth: {"token" if token else "unauthenticated"} (delay: {rate_delay}s)')
    print(f'Already processed: {len(stats)}')
    print(f'Starting from offset: {offset}, batch: {batch_size}')
    print()

    releases = get_releases_with_discogs_id(limit=batch_size, offset=offset)
    if not releases:
        print('No more releases to process.')
        write_output(stats)
        return

    print(f'Loaded {len(releases)} releases')

    enriched = 0
    skipped = 0

    for i, release in enumerate(releases):
        rid = str(release['id'])
        discogs_id = release['discogs_id']

        if rid in stats:
            continue

        result = get_release_stats(discogs_id, token)
        time.sleep(rate_delay)

        if result:
            stats[rid] = result
            enriched += 1
        else:
            stats[rid] = None
            skipped += 1

        if (i + 1) % 25 == 0:
            progress['stats'] = stats
            progress['offset'] = offset + i + 1
            save_progress(progress)
            found = len([v for v in stats.values() if v is not None])
            print(f'  [{i+1}/{len(releases)}] Enriched: {enriched}, Skipped: {skipped} (Total: {found})')

    # Final save
    progress['stats'] = stats
    progress['offset'] = offset + len(releases)
    save_progress(progress)

    found = len([v for v in stats.values() if v is not None])
    print(f'\nBatch complete: {enriched} enriched, {skipped} skipped')
    print(f'Total: {found} releases with community stats')

    write_output(stats)


def write_output(stats):
    """Write enriched data to JSON."""
    found = {k: v for k, v in stats.items() if v is not None}

    # Compute interesting stats
    if found:
        most_wanted = sorted(found.items(), key=lambda x: -x[1]['want'])[:20]
        most_owned = sorted(found.items(), key=lambda x: -x[1]['have'])[:20]
        highest_rated = sorted(
            [(k, v) for k, v in found.items() if v['rating_count'] >= 5],
            key=lambda x: -x[1]['rating_average']
        )[:20]
    else:
        most_wanted = most_owned = highest_rated = []

    output = {
        'meta': {
            'source': 'Discogs API community stats',
            'total_enriched': len(found),
            'total_searched': len(stats),
        },
        'stats': found,
        'rankings': {
            'most_wanted': [{'id': k, **v} for k, v in most_wanted],
            'most_owned': [{'id': k, **v} for k, v in most_owned],
            'highest_rated': [{'id': k, **v} for k, v in highest_rated],
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)

    print(f'Written to {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
