#!/usr/bin/env python3
"""
Generate release particle positions for the 3D world.
Each release gets positioned near its genre(s) with small jitter.
Outputs a compact binary format for efficient frontend loading.
"""

import json
import os
import struct
from collections import defaultdict

RELEASES_JSONL = os.path.expanduser("~/repos/discoworld/data/processed/electronic_releases.jsonl")
WORLD_JSON = os.path.expanduser("~/repos/discoworld/packages/web/public/data/world.json")
OUTPUT_JSON = os.path.expanduser("~/repos/discoworld/packages/web/public/data/release_particles.json")

# Load genre positions from world.json
with open(WORLD_JSON) as f:
    world = json.load(f)

# Build style → genre position mapping
# Discogs styles → nearest Ishkur genre
# This is an approximate mapping — Discogs styles don't 1:1 map to Ishkur slugs
genre_positions = {}
for g in world["genres"]:
    genre_positions[g["name"].lower()] = {"x": g["x"], "y": g["y"], "z": g["z"], "color": g["color"]}
    # Also map scene names
    if g["scene"].lower() not in genre_positions:
        genre_positions[g["scene"].lower()] = {"x": g["x"], "y": g["y"], "z": g["z"], "color": g["color"]}

# Discogs style → position mapping (fuzzy)
STYLE_MAPPING = {
    "house": "house", "deep house": "deep house", "acid house": "acid house",
    "tech house": "tech house", "progressive house": "progressive house",
    "techno": "techno", "minimal": "minimal techno", "minimal techno": "minimal techno",
    "dub techno": "dub techno", "acid": "acid techno",
    "trance": "trance", "goa trance": "goa trance", "psy-trance": "psytrance",
    "progressive trance": "progressive trance",
    "drum n bass": "drum and bass", "jungle": "jungle",
    "dubstep": "dubstep", "uk garage": "2-step garage",
    "ambient": "ambient", "downtempo": "downtempo", "trip hop": "trip hop",
    "idm": "idm", "breakbeat": "breakbeat", "big beat": "big beat",
    "industrial": "industrial", "ebm": "ebm",
    "disco": "disco", "italo-disco": "italo disco", "nu-disco": "nu-disco",
    "synth-pop": "synthpop", "electro": "electro",
    "gabber": "gabber", "hardcore": "gabber", "happy hardcore": "happy hardcore",
    "hardstyle": "hardstyle", "grime": "grime",
    "noise": "noise", "experimental": "experimental",
    "glitch": "glitch", "vaporwave": "vaporwave",
    "bass music": "dubstep", "breaks": "breakbeat",
}

# Seed random for reproducibility
import random
random.seed(42)

def get_position_for_styles(styles):
    """Get average position for a list of Discogs styles."""
    positions = []
    for style in styles:
        key = style.lower()
        # Direct match
        if key in genre_positions:
            positions.append(genre_positions[key])
            continue
        # Mapped match
        mapped = STYLE_MAPPING.get(key)
        if mapped and mapped in genre_positions:
            positions.append(genre_positions[mapped])
            continue
        # Partial match
        for gname, gpos in genre_positions.items():
            if key in gname or gname in key:
                positions.append(gpos)
                break

    if not positions:
        # Default to center with large jitter
        return {"x": random.uniform(-30, 30), "y": 0, "z": random.uniform(-30, 30), "color": "#444444"}

    # Average position
    x = sum(p["x"] for p in positions) / len(positions)
    z = sum(p["z"] for p in positions) / len(positions)
    color = positions[0]["color"]

    # Add jitter (proportional to genre cluster size)
    jitter = 3.0
    x += random.uniform(-jitter, jitter)
    z += random.uniform(-jitter, jitter)

    return {"x": x, "y": 0, "z": z, "color": color}


# Process releases
print("Generating release particles...")
particles = []
MAX_PARTICLES = 50000  # Limit for frontend performance
vinyl_only = True

count = 0
with open(RELEASES_JSONL) as f:
    for line in f:
        r = json.loads(line)

        # Must have YouTube for playability
        if not r.get("videos"):
            continue

        # Prefer vinyl
        if vinyl_only:
            is_vinyl = False
            for fmt in r.get("formats", []):
                name = fmt.get("name", "").lower()
                descs = [d.lower() for d in fmt.get("descriptions", [])]
                if name == "vinyl" or '12"' in descs or '10"' in descs or '7"' in descs:
                    is_vinyl = True
                    break
            if not is_vinyl:
                continue

        pos = get_position_for_styles(r.get("styles", []))
        year = int(r["year"]) if r.get("year", "").isdigit() else 2000

        artists_str = ", ".join(a["name"] for a in r.get("artists", [])[:2])
        label_str = r["labels"][0]["name"] if r.get("labels") else ""

        particles.append({
            "id": r["id"],
            "x": round(pos["x"], 2),
            "z": round(pos["z"], 2),
            "year": year,
            "color": pos["color"],
            "artist": artists_str[:50],
            "title": r["title"][:60],
            "label": label_str[:40],
            "yt": r["videos"][0]["url"] if r["videos"] else "",
        })

        count += 1
        if count >= MAX_PARTICLES:
            break
        if count % 10000 == 0:
            print(f"  {count:,} particles generated...")

print(f"\nGenerated {len(particles)} release particles")

output = {
    "meta": {"count": len(particles), "vinyl_only": vinyl_only},
    "particles": particles,
}

with open(OUTPUT_JSON, "w") as f:
    json.dump(output, f)

print(f"Written to {OUTPUT_JSON} ({os.path.getsize(OUTPUT_JSON) / 1024 / 1024:.1f} MB)")
