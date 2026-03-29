"""
Enrich cities.json with artist/label data from artist_cities.json.

Merges the output of extract_artist_cities.py into the existing
cities.json used by the EarthGlobe component.

Usage:
    python3 enrich_cities.py [--artist-cities PATH] [--cities PATH]
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
ARTIST_CITIES_PATH = DATA_DIR / "artist_cities.json"
CITIES_JSON_PATH = (
    Path(__file__).resolve().parent.parent / "web" / "public" / "data" / "cities.json"
)


def _slugify(name: str) -> str:
    """Convert city name to a URL-friendly slug."""
    return (
        name.lower()
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ä", "a")
        .replace("ã", "a")
        .replace("é", "e")
        .replace(" ", "_")
    )


def enrich(
    artist_cities_path: Path = ARTIST_CITIES_PATH,
    cities_json_path: Path = CITIES_JSON_PATH,
) -> dict:
    """
    Merge artist_cities.json data into cities.json.

    - Existing cities get enriched with artists, labels, artist_count, label_count
    - New cities from artist_cities.json are added
    - Returns the merged data (also written to cities_json_path)
    """
    # Load artist cities data
    if not artist_cities_path.exists():
        print(f"[enrich_cities] artist_cities.json not found at {artist_cities_path}")
        print("  Run extract_artist_cities.py first.")
        return {}

    with open(artist_cities_path) as f:
        artist_data = json.load(f)

    # Build lookup by city name (lowercase)
    artist_by_city: dict[str, dict] = {}
    for ac in artist_data.get("cities", []):
        key = ac["city"].lower()
        artist_by_city[key] = ac

    # Load existing cities.json
    if cities_json_path.exists():
        with open(cities_json_path) as f:
            cities_data = json.load(f)
    else:
        cities_data = {
            "meta": {
                "version": "1.0.0",
                "description": "Electronic music cities",
                "source": "enrich_cities.py",
            },
            "cities": [],
        }

    existing_cities = cities_data.get("cities", [])
    existing_by_id: dict[str, dict] = {c["id"]: c for c in existing_cities}
    existing_by_name: dict[str, str] = {c["name"].lower(): c["id"] for c in existing_cities}

    enriched_count = 0
    added_count = 0

    # Enrich existing cities
    for city in existing_cities:
        city_name_lower = city["name"].lower()
        ac = artist_by_city.get(city_name_lower)
        if ac:
            city["artists"] = ac.get("artists", [])
            city["labels"] = ac.get("labels", [])
            city["artist_count"] = ac.get("artist_count", 0)
            city["label_count"] = ac.get("label_count", 0)
            # Update release_count if the DB scan found more
            if ac.get("release_count", 0) > city.get("release_count", 0):
                city["release_count"] = ac["release_count"]
            enriched_count += 1

    # Add new cities not in existing data
    for ac in artist_data.get("cities", []):
        city_name_lower = ac["city"].lower()
        if city_name_lower not in existing_by_name:
            city_id = _slugify(ac["city"])
            # Skip if id collision (shouldn't happen but be safe)
            if city_id in existing_by_id:
                continue

            new_city = {
                "id": city_id,
                "name": ac["city"],
                "country": _guess_country(ac["city"]),
                "lat": ac["lat"],
                "lng": ac["lng"],
                "genres": [],  # Will need manual curation or genre inference
                "release_count": ac.get("release_count", 0),
                "artists": ac.get("artists", []),
                "labels": ac.get("labels", []),
                "artist_count": ac.get("artist_count", 0),
                "label_count": ac.get("label_count", 0),
                "description": f"Electronic music scene — {ac.get('artist_count', 0)} known artists",
            }
            existing_cities.append(new_city)
            existing_by_id[city_id] = new_city
            existing_by_name[city_name_lower] = city_id
            added_count += 1

    # Update meta
    cities_data["meta"]["enriched_at"] = datetime.now(timezone.utc).isoformat()
    cities_data["meta"]["artist_source"] = str(artist_cities_path.name)
    cities_data["meta"]["total_cities"] = len(existing_cities)
    cities_data["cities"] = existing_cities

    # Write
    cities_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cities_json_path, "w") as f:
        json.dump(cities_data, f, indent=2, ensure_ascii=False)

    print(f"[enrich_cities] Enriched {enriched_count} existing cities")
    print(f"[enrich_cities] Added {added_count} new cities")
    print(f"[enrich_cities] Total: {len(existing_cities)} cities → {cities_json_path}")

    return cities_data


# ---------------------------------------------------------------------------
# Country guesser (best-effort for new cities)
# ---------------------------------------------------------------------------

_CITY_COUNTRY_MAP = {
    "detroit": "US", "chicago": "US", "new york": "US", "los angeles": "US",
    "san francisco": "US", "atlanta": "US", "montreal": "Canada",
    "berlin": "Germany", "cologne": "Germany", "frankfurt": "Germany",
    "düsseldorf": "Germany", "hamburg": "Germany", "munich": "Germany",
    "mannheim": "Germany", "leipzig": "Germany",
    "london": "UK", "sheffield": "UK", "manchester": "UK", "bristol": "UK",
    "leeds": "UK", "glasgow": "UK", "nottingham": "UK", "birmingham": "UK",
    "leicester": "UK", "edinburgh": "UK", "belfast": "UK",
    "paris": "France",
    "amsterdam": "Netherlands", "rotterdam": "Netherlands",
    "the hague": "Netherlands", "groningen": "Netherlands",
    "tokyo": "Japan", "osaka": "Japan", "sapporo": "Japan",
    "stockholm": "Sweden", "copenhagen": "Denmark", "helsinki": "Finland",
    "reykjavik": "Iceland",
    "lisbon": "Portugal", "barcelona": "Spain",
    "ghent": "Belgium", "brussels": "Belgium",
    "zürich": "Switzerland", "vienna": "Austria",
    "rome": "Italy", "naples": "Italy", "turin": "Italy",
    "bucharest": "Romania", "zagreb": "Croatia", "warsaw": "Poland",
    "prague": "Czech Republic", "athens": "Greece",
    "moscow": "Russia", "kyiv": "Ukraine", "tbilisi": "Georgia",
    "tel aviv": "Israel", "beirut": "Lebanon",
    "mumbai": "India", "new delhi": "India", "goa": "India",
    "beijing": "China", "shanghai": "China",
    "seoul": "South Korea", "singapore": "Singapore",
    "melbourne": "Australia", "sydney": "Australia",
    "são paulo": "Brazil", "bogota": "Colombia",
    "mexico city": "Mexico",
    "johannesburg": "South Africa", "durban": "South Africa",
    "cape town": "South Africa",
    "kampala": "Uganda", "nairobi": "Kenya", "lagos": "Nigeria",
}


def _guess_country(city_name: str) -> str:
    """Best-effort country lookup for a city name."""
    return _CITY_COUNTRY_MAP.get(city_name.lower(), "Unknown")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich cities.json with artist data")
    parser.add_argument(
        "--artist-cities", type=Path, default=ARTIST_CITIES_PATH,
        help="Path to artist_cities.json",
    )
    parser.add_argument(
        "--cities", type=Path, default=CITIES_JSON_PATH,
        help="Path to cities.json",
    )
    args = parser.parse_args()

    enrich(artist_cities_path=args.artist_cities, cities_json_path=args.cities)
