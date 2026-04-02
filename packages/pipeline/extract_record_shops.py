"""Extract record shops worldwide from OpenStreetMap via Overpass API.

Queries all nodes tagged shop=music, extracts name/lat/lng/metadata,
and writes to packages/web/public/data/record_shops.json.
"""

import json
import sys
from pathlib import Path

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Split world into regional bounding boxes to avoid timeout
# Format: (south, west, north, east)
REGIONS = [
    ("Europe West", (35, -12, 60, 15)),
    ("Europe East", (35, 15, 72, 45)),
    ("Scandinavia+UK", (54, -12, 72, 15)),
    ("North America East", (20, -100, 55, -60)),
    ("North America West", (20, -140, 55, -100)),
    ("South America", (-60, -85, 15, -30)),
    ("East Asia", (20, 100, 50, 150)),
    ("Southeast Asia + Oceania", (-50, 100, 20, 180)),
    ("Africa + Middle East", (-40, -20, 40, 60)),
    ("Central Asia + India", (5, 60, 55, 100)),
]

OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "web" / "public" / "data" / "record_shops.json"
)


def extract_shops() -> list[dict]:
    """Query Overpass API and return parsed shop list."""
    print("Querying Overpass API for music shops (by region)...")
    import time

    all_elements = []
    for region_name, (south, west, north, east) in REGIONS:
        query = f'[out:json][timeout:90];(node["shop"="music"]({south},{west},{north},{east});way["shop"="music"]({south},{west},{north},{east});node["shop"="vinyl"]({south},{west},{north},{east});way["shop"="vinyl"]({south},{west},{north},{east});node["shop"="records"]({south},{west},{north},{east});way["shop"="records"]({south},{west},{north},{east});node["shop"~"^(hifi|second_hand)$"]["music:vinyl"="yes"]({south},{west},{north},{east}););out center body;'
        print(f"  {region_name} ({south},{west},{north},{east})...", end=" ", flush=True)
        for attempt in range(3):
            try:
                resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=120)
                if resp.status_code == 429:
                    wait = 15 * (attempt + 1)
                    print(f"429, waiting {wait}s...", end=" ", flush=True)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                elems = resp.json().get("elements", [])
                print(f"{len(elems)} elements")
                all_elements.extend(elems)
                break
            except Exception as e:
                if attempt == 2:
                    print(f"FAILED: {e}")
                else:
                    time.sleep(10)
        time.sleep(8)  # Be nice to Overpass

    elements = all_elements
    print(f"  Total raw elements: {len(elements)}")

    shops = []
    seen = set()

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name", "").strip()
        if not name:
            continue

        # Get coordinates (center for ways, direct for nodes)
        if el["type"] == "way" and "center" in el:
            lat = el["center"]["lat"]
            lng = el["center"]["lon"]
        elif el["type"] == "node":
            lat = el.get("lat")
            lng = el.get("lon")
        else:
            continue

        if lat is None or lng is None:
            continue

        # Dedup by name+coords (rounded to 4 decimals)
        key = (name.lower(), round(lat, 4), round(lng, 4))
        if key in seen:
            continue
        seen.add(key)

        shop = {
            "id": el["id"],
            "name": name,
            "lat": round(lat, 5),
            "lng": round(lng, 5),
        }

        # Optional fields
        city = tags.get("addr:city", "")
        country = tags.get("addr:country", "")
        website = tags.get("website", tags.get("contact:website", ""))
        opening_hours = tags.get("opening_hours", "")
        second_hand = tags.get("second_hand", "")
        shop_type = tags.get("shop", "")
        vinyl = (
            shop_type == "vinyl" or
            "vinyl" in tags.get("music:genre", "").lower() or
            tags.get("music:vinyl") == "yes" or
            "vinyl" in name.lower() or
            "record" in name.lower() or
            second_hand == "yes"
        )
        phone = tags.get("phone", tags.get("contact:phone", ""))
        street = tags.get("addr:street", "")
        housenumber = tags.get("addr:housenumber", "")

        if city:
            shop["city"] = city
        if country:
            shop["country"] = country
        if website:
            shop["website"] = website
        if opening_hours:
            shop["opening_hours"] = opening_hours
        if vinyl:
            shop["vinyl"] = True
        if phone:
            shop["phone"] = phone
        if street:
            addr = f"{street} {housenumber}".strip()
            shop["address"] = addr

        shops.append(shop)

    # Sort by name
    shops.sort(key=lambda s: s["name"].lower())
    return shops


def main():
    shops = extract_shops()
    print(f"  Parsed shops: {len(shops)}")

    vinyl_count = sum(1 for s in shops if s.get("vinyl"))
    print(f"  Vinyl/second-hand flagged: {vinyl_count}")

    # Compute country stats
    countries = {}
    for s in shops:
        c = s.get("country", "unknown")
        countries[c] = countries.get(c, 0) + 1

    output = {
        "meta": {
            "source": "OpenStreetMap via Overpass API",
            "license": "ODbL",
            "total": len(shops),
            "vinyl_flagged": vinyl_count,
        },
        "shops": shops,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, ensure_ascii=False)

    print(f"  Saved to {OUTPUT_PATH}")
    print(f"  Top countries: {sorted(countries.items(), key=lambda x: -x[1])[:10]}")


if __name__ == "__main__":
    main()
