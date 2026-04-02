#!/usr/bin/env python3
"""
Extract label locations from Discogs labels.xml.gz dump.

Parses contactinfo fields to extract city/country/coordinates,
then cross-references with existing DB labels to enrich the Earth Globe.
Output: data/processed/label_locations.json
"""

import gzip
import json
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter

# Known city patterns for geocoding (major music cities)
CITY_GEOCODING = {
    'detroit': {'lat': 42.33, 'lng': -83.04, 'country': 'US'},
    'berlin': {'lat': 52.52, 'lng': 13.41, 'country': 'DE'},
    'london': {'lat': 51.51, 'lng': -0.13, 'country': 'GB'},
    'new york': {'lat': 40.71, 'lng': -74.01, 'country': 'US'},
    'chicago': {'lat': 41.88, 'lng': -87.63, 'country': 'US'},
    'amsterdam': {'lat': 52.37, 'lng': 4.90, 'country': 'NL'},
    'paris': {'lat': 48.86, 'lng': 2.35, 'country': 'FR'},
    'tokyo': {'lat': 35.68, 'lng': 139.69, 'country': 'JP'},
    'los angeles': {'lat': 34.05, 'lng': -118.24, 'country': 'US'},
    'manchester': {'lat': 53.48, 'lng': -2.24, 'country': 'GB'},
    'bristol': {'lat': 51.45, 'lng': -2.59, 'country': 'GB'},
    'glasgow': {'lat': 55.86, 'lng': -4.25, 'country': 'GB'},
    'sheffield': {'lat': 53.38, 'lng': -1.47, 'country': 'GB'},
    'brussels': {'lat': 50.85, 'lng': 4.35, 'country': 'BE'},
    'cologne': {'lat': 50.94, 'lng': 6.96, 'country': 'DE'},
    'hamburg': {'lat': 53.55, 'lng': 9.99, 'country': 'DE'},
    'munich': {'lat': 48.14, 'lng': 11.58, 'country': 'DE'},
    'frankfurt': {'lat': 50.11, 'lng': 8.68, 'country': 'DE'},
    'barcelona': {'lat': 41.39, 'lng': 2.17, 'country': 'ES'},
    'madrid': {'lat': 40.42, 'lng': -3.70, 'country': 'ES'},
    'lisbon': {'lat': 38.72, 'lng': -9.14, 'country': 'PT'},
    'melbourne': {'lat': -37.81, 'lng': 144.96, 'country': 'AU'},
    'sydney': {'lat': -33.87, 'lng': 151.21, 'country': 'AU'},
    'toronto': {'lat': 43.65, 'lng': -79.38, 'country': 'CA'},
    'montreal': {'lat': 45.50, 'lng': -73.57, 'country': 'CA'},
    'san francisco': {'lat': 37.77, 'lng': -122.42, 'country': 'US'},
    'seattle': {'lat': 47.61, 'lng': -122.33, 'country': 'US'},
    'atlanta': {'lat': 33.75, 'lng': -84.39, 'country': 'US'},
    'miami': {'lat': 25.76, 'lng': -80.19, 'country': 'US'},
    'portland': {'lat': 45.52, 'lng': -122.68, 'country': 'US'},
    'philadelphia': {'lat': 39.95, 'lng': -75.17, 'country': 'US'},
    'rotterdam': {'lat': 51.92, 'lng': 4.48, 'country': 'NL'},
    'den haag': {'lat': 52.08, 'lng': 4.30, 'country': 'NL'},
    'the hague': {'lat': 52.08, 'lng': 4.30, 'country': 'NL'},
    'copenhagen': {'lat': 55.68, 'lng': 12.57, 'country': 'DK'},
    'stockholm': {'lat': 59.33, 'lng': 18.07, 'country': 'SE'},
    'oslo': {'lat': 59.91, 'lng': 10.75, 'country': 'NO'},
    'helsinki': {'lat': 60.17, 'lng': 24.94, 'country': 'FI'},
    'vienna': {'lat': 48.21, 'lng': 16.37, 'country': 'AT'},
    'zurich': {'lat': 47.38, 'lng': 8.54, 'country': 'CH'},
    'milan': {'lat': 45.46, 'lng': 9.19, 'country': 'IT'},
    'rome': {'lat': 41.90, 'lng': 12.50, 'country': 'IT'},
    'naples': {'lat': 40.85, 'lng': 14.27, 'country': 'IT'},
    'seoul': {'lat': 37.57, 'lng': 126.98, 'country': 'KR'},
    'beijing': {'lat': 39.90, 'lng': 116.40, 'country': 'CN'},
    'shanghai': {'lat': 31.23, 'lng': 121.47, 'country': 'CN'},
    'mumbai': {'lat': 19.08, 'lng': 72.88, 'country': 'IN'},
    'cape town': {'lat': -33.93, 'lng': 18.42, 'country': 'ZA'},
    'johannesburg': {'lat': -26.20, 'lng': 28.05, 'country': 'ZA'},
    'lagos': {'lat': 6.52, 'lng': 3.38, 'country': 'NG'},
    'sao paulo': {'lat': -23.55, 'lng': -46.63, 'country': 'BR'},
    'rio de janeiro': {'lat': -22.91, 'lng': -43.17, 'country': 'BR'},
    'buenos aires': {'lat': -34.60, 'lng': -58.38, 'country': 'AR'},
    'mexico city': {'lat': 19.43, 'lng': -99.13, 'country': 'MX'},
    'bogota': {'lat': 4.71, 'lng': -74.07, 'country': 'CO'},
    'tbilisi': {'lat': 41.72, 'lng': 44.79, 'country': 'GE'},
    'beirut': {'lat': 33.89, 'lng': 35.50, 'country': 'LB'},
    'tel aviv': {'lat': 32.09, 'lng': 34.78, 'country': 'IL'},
    'budapest': {'lat': 47.50, 'lng': 19.04, 'country': 'HU'},
    'prague': {'lat': 50.08, 'lng': 14.44, 'country': 'CZ'},
    'warsaw': {'lat': 52.23, 'lng': 21.01, 'country': 'PL'},
    'athens': {'lat': 37.98, 'lng': 23.73, 'country': 'GR'},
    'istanbul': {'lat': 41.01, 'lng': 28.98, 'country': 'TR'},
    'dublin': {'lat': 53.35, 'lng': -6.26, 'country': 'IE'},
    'edinburgh': {'lat': 55.95, 'lng': -3.19, 'country': 'GB'},
    'leeds': {'lat': 53.80, 'lng': -1.55, 'country': 'GB'},
    'birmingham': {'lat': 52.48, 'lng': -1.90, 'country': 'GB'},
    'nottingham': {'lat': 52.95, 'lng': -1.15, 'country': 'GB'},
    'brighton': {'lat': 50.82, 'lng': -0.14, 'country': 'GB'},
    'leipzig': {'lat': 51.34, 'lng': 12.37, 'country': 'DE'},
    'düsseldorf': {'lat': 51.23, 'lng': 6.78, 'country': 'DE'},
    'dusseldorf': {'lat': 51.23, 'lng': 6.78, 'country': 'DE'},
    'costa mesa': {'lat': 33.64, 'lng': -117.92, 'country': 'US'},
    'san diego': {'lat': 32.72, 'lng': -117.16, 'country': 'US'},
    'austin': {'lat': 30.27, 'lng': -97.74, 'country': 'US'},
    'nashville': {'lat': 36.16, 'lng': -86.78, 'country': 'US'},
    'denver': {'lat': 39.74, 'lng': -104.98, 'country': 'US'},
    'minneapolis': {'lat': 44.98, 'lng': -93.27, 'country': 'US'},
    'oakland': {'lat': 37.80, 'lng': -122.27, 'country': 'US'},
    'brooklyn': {'lat': 40.68, 'lng': -73.94, 'country': 'US'},
    'queens': {'lat': 40.73, 'lng': -73.79, 'country': 'US'},
}

# Country name → ISO code mapping
COUNTRY_CODES = {
    'usa': 'US', 'united states': 'US', 'u.s.a.': 'US', 'u.s.': 'US',
    'uk': 'GB', 'united kingdom': 'GB', 'england': 'GB', 'scotland': 'GB', 'wales': 'GB',
    'germany': 'DE', 'deutschland': 'DE',
    'france': 'FR',
    'netherlands': 'NL', 'holland': 'NL', 'the netherlands': 'NL',
    'belgium': 'BE', 'belgique': 'BE',
    'japan': 'JP',
    'canada': 'CA',
    'australia': 'AU',
    'italy': 'IT', 'italia': 'IT',
    'spain': 'ES', 'españa': 'ES',
    'portugal': 'PT',
    'sweden': 'SE', 'sverige': 'SE',
    'denmark': 'DK', 'danmark': 'DK',
    'norway': 'NO', 'norge': 'NO',
    'finland': 'FI', 'suomi': 'FI',
    'austria': 'AT', 'österreich': 'AT',
    'switzerland': 'CH', 'schweiz': 'CH', 'suisse': 'CH',
    'ireland': 'IE',
    'brazil': 'BR', 'brasil': 'BR',
    'argentina': 'AR',
    'mexico': 'MX', 'méxico': 'MX',
    'south korea': 'KR', 'korea': 'KR',
    'china': 'CN',
    'india': 'IN',
    'south africa': 'ZA',
    'greece': 'GR',
    'turkey': 'TR', 'türkiye': 'TR',
    'poland': 'PL', 'polska': 'PL',
    'czech republic': 'CZ', 'czechia': 'CZ',
    'hungary': 'HU',
    'romania': 'RO',
    'russia': 'RU',
    'ukraine': 'UA',
    'georgia': 'GE',
    'israel': 'IL',
    'lebanon': 'LB',
    'colombia': 'CO',
    'chile': 'CL',
    'nigeria': 'NG',
    'new zealand': 'NZ',
}


def extract_city_from_contact(contact_info):
    """Parse contactinfo to extract city and country."""
    if not contact_info:
        return None, None

    text = contact_info.replace('\r\n', '\n').replace('\r', '\n')
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    city = None
    country = None

    # Strategy 1: Look for known cities in any line
    text_lower = text.lower()
    for city_name, geo in CITY_GEOCODING.items():
        if city_name in text_lower:
            city = city_name
            country = geo['country']
            break

    # Strategy 2: Look for country in last lines
    if not country:
        for line in reversed(lines[-5:]):
            line_lower = line.lower().strip().rstrip('.')
            if line_lower in COUNTRY_CODES:
                country = COUNTRY_CODES[line_lower]
                break

    # Strategy 3: Look for US state abbreviation patterns
    if not country:
        for line in lines:
            if re.search(r'\b[A-Z]{2}\s+\d{5}', line):
                country = 'US'
                break
            if re.search(r'\b[A-Z]\d[A-Z]\s*\d[A-Z]\d', line):
                country = 'CA'
                break

    return city, country


def geocode_label(city, country):
    """Return lat/lng for a label based on city match."""
    if city and city.lower() in CITY_GEOCODING:
        return CITY_GEOCODING[city.lower()]
    return None


def parse_labels(dump_path, limit=None):
    """Stream-parse labels XML and extract locations."""
    labels = []
    count = 0
    skipped = 0

    print(f'Parsing {dump_path}...')
    with gzip.open(dump_path, 'rb') as f:
        for event, elem in ET.iterparse(f, events=('end',)):
            if elem.tag != 'label':
                continue

            label_id = elem.findtext('id')
            name = elem.findtext('name')
            contact = elem.findtext('contactinfo')
            profile = elem.findtext('profile') or ''

            if not label_id or not name:
                elem.clear()
                continue

            city, country = extract_city_from_contact(contact)

            # Also check profile for city mentions if contact didn't work
            if not city and profile:
                profile_lower = profile.lower()
                for city_name in CITY_GEOCODING:
                    if city_name in profile_lower:
                        city = city_name
                        if not country:
                            country = CITY_GEOCODING[city_name]['country']
                        break

            geo = geocode_label(city, country)

            if geo:
                labels.append({
                    'id': int(label_id),
                    'name': name,
                    'city': city.title() if city else None,
                    'country': geo.get('country', country),
                    'lat': geo['lat'],
                    'lng': geo['lng'],
                })
                count += 1
            elif country:
                # We have a country but no city geo
                labels.append({
                    'id': int(label_id),
                    'name': name,
                    'city': None,
                    'country': country,
                    'lat': None,
                    'lng': None,
                })
                skipped += 1

            elem.clear()

            if limit and count + skipped >= limit:
                break

            if (count + skipped) % 50000 == 0:
                print(f'  Processed {count + skipped} labels... ({count} geocoded, {skipped} country-only)')

    return labels, count, skipped


def cross_reference_db(labels, db_path):
    """Cross-reference with DiscoWorld DB to find labels with releases."""
    if not Path(db_path).exists():
        print(f'DB not found at {db_path}, skipping cross-reference')
        return labels

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all labels with release counts
    cursor.execute("""
        SELECT label, COUNT(*) as cnt
        FROM releases
        WHERE label IS NOT NULL AND label != ''
        GROUP BY label
        HAVING cnt >= 3
        ORDER BY cnt DESC
    """)
    db_labels = {row[0].lower(): row[1] for row in cursor.fetchall()}
    conn.close()

    # Enrich labels with release counts
    enriched = []
    for label in labels:
        name_lower = label['name'].lower()
        if name_lower in db_labels:
            label['release_count'] = db_labels[name_lower]
            enriched.append(label)

    return enriched


def main():
    base = Path(__file__).parent.parent.parent
    dump_path = base / 'data' / 'discogs-dump' / 'discogs_20260301_labels.xml.gz'
    db_path = base / 'data' / 'discoworld.db'
    output_path = base / 'data' / 'processed' / 'label_locations.json'

    if not dump_path.exists():
        print(f'Labels dump not found: {dump_path}')
        sys.exit(1)

    labels, geocoded, country_only = parse_labels(dump_path)
    print(f'\nTotal parsed: {geocoded} geocoded, {country_only} country-only')

    # Cross-reference with DB
    enriched = cross_reference_db(labels, db_path)
    print(f'Labels with releases in DB: {len(enriched)}')

    # Stats
    city_counts = Counter(l['city'] for l in enriched if l['city'])
    country_counts = Counter(l['country'] for l in enriched if l['country'])
    print(f'\nTop 20 cities:')
    for city, cnt in city_counts.most_common(20):
        print(f'  {city}: {cnt}')
    print(f'\nTop 15 countries:')
    for cc, cnt in country_counts.most_common(15):
        print(f'  {cc}: {cnt}')

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        'labels': enriched,
        'stats': {
            'total_geocoded': geocoded,
            'total_country_only': country_only,
            'matched_with_db': len(enriched),
            'cities': dict(city_counts.most_common(50)),
            'countries': dict(country_counts.most_common()),
        },
    }
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f'\nWritten to {output_path} ({len(enriched)} labels)')


if __name__ == '__main__':
    main()
