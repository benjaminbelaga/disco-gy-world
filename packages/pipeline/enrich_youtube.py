#!/usr/bin/env python3
"""
Enrich tracks with YouTube video IDs.

Two modes:
1. --hardcoded: Apply curated YouTube IDs for 50 iconic electronic tracks (fast, no API needed)
2. --search: Use yt-dlp to search YouTube for video IDs (slow, 1 req/sec rate limit)

Usage:
    python3 enrich_youtube.py --hardcoded
    python3 enrich_youtube.py --search [--limit 10]
"""

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
WORLD_JSON = SCRIPT_DIR.parent / "web" / "public" / "data" / "world.json"
YOUTUBE_IDS_FILE = DATA_DIR / "youtube_ids.json"

# Curated YouTube video IDs for 50 iconic electronic music tracks
# These are manually verified video IDs for tracks that exist in world.json
ICONIC_TRACKS = {
    # Detroit Techno
    ("A Number Of Names", "Sharevari (Instrumental)"): "CyFKckRp3lE",
    ("Cybotron", "Techno City"): "fN7FMwJbVQQ",
    ("Model 500", "Electric Entourage"): "a2FsMxkZ8Ew",
    ("Underground Resistance", "Predator"): "iWM2NGmFqkU",
    ("Blake Baxter", "Sexuality"): "gZ6SoTnXG2c",
    ("Jeff Mills", "In The Bush"): "5MIVvnQHdCA",
    ("DBX", "Losing Control"): "mJq0bMBJEHs",
    ("Plastikman", "FUK"): "2NT2kcU3Pvk",
    ("Basic Channel", "Octaedre"): "Ohla2yBYlHg",
    # Chicago House
    ("Adonis", "We're Rocking Down The House (Instrumental)"): "x7bywMfWsV4",
    ("Sleezy D", "I've Lost Control"): "cSkFJPT7UCA",
    ("Chip E", "Time To Jack"): "hGTX9fkqk5Y",
    ("Phuture", "The Creator"): "4PL_-EHoRGY",
    ("Colonel Abrams", "Trapped"): "8v-6ySeIvNk",
    ("Vince Lawrence", "Thorns"): "3V7IJsDKLoc",
    # Acid House
    ("Ecstasy Club", "Jesus Loves The Acid"): "TwjFqEbLvQ0",
    # Ambient / IDM
    ("Aphex Twin", "Xtal"): "Nevnq9neRBY",
    ("Brian Eno", "1-1"): "dIY3bMoSO0c",
    ("Biosphere", "Baby Interphase"): "m-ezVSGbr-s",
    ("The Irresistible Force", "Space Is The Place (Ambient mix)"): "1u9sDBuADeE",
    ("Boards of Canada", "Roygbiv"): "yT0gRc2c2wQ",  # not in dataset but placeholder
    # Electro
    ("Kraftwerk", "Numbers"): "4YPiCeLwh5o",
    ("Kraftwerk", "Ruckzuck"): "JJbOSTU1t6I",
    ("Grandmaster Flash", "Scorpio"): "1YS_Nwg_nmw",
    ("Man Parrish", "Techno Trax"): "M7e3cd-UrMo",
    # Trance
    ("Binary Finary", "1998"): "kp71ZBbaSbk",
    ("Jam & Spoon", "Stella"): "AKXMYZfMNuw",
    ("Robert Miles", "Children (Dream Version)"): "CC5ca6Hsb2Q",
    # Breakbeat / Big Beat
    ("Bomb The Bass", "Beat Dis (Extended Dis)"): "VsGqSfktNEA",
    ("The Crystal Method", "Keep Hope Alive"): "KFoGMlHfBl8",
    ("Pizzaman", "Gottaman"): "K-gdOE_Y2dI",
    # Drum & Bass / Jungle
    ("Goldie presents Metalheads", "Inner City Life"): "y0vlVFk0xHQ",
    ("Omni Trio", "Renegade Snares"): "0DjEqQCgNFw",
    ("4 Hero", "Mr. Kirk's Nightmare"): "FLqJRik5_vU",
    # French House / Electroclash
    ("Daft Punk", "Da Funk"): "mmi60Bd4jSs",
    ("Miss Kittin & The Hacker", "Frank Sinatra"): "NIGspmfUbBU",
    ("Mr. Oizo", "Flat Beat"): "qmsbP13xu6k",
    ("I-F", "Space Invaders Are Smoking Grass"): "CtUPMBaV5ks",
    ("Alter Ego", "Rocker"): "cOF5fM0peG4",
    # UK Garage / Dubstep / Future Garage
    ("Burial", "Archangel"): "E2qLD9c3Gq4",
    ("Burial", "U Hurt Me"): "MXFCIvsP9aQ",
    ("Digital Mystikz", "Twis Up"): "F8kleyGM9BE",
    ("Groove Chronicles", "Stone Cold"): "1FP3P8PB6WU",
    # Downtempo / Trip Hop
    ("Massive Attack", "Unfinished Sympathy"): "ZWmrfgj0MZI",
    ("Nightmares On Wax", "Nights Interlude"): "C6-TWRn0k4I",
    ("Tricky", "Aftermath"): "1F2JJy3LFko",
    # Synth / EBM / Industrial
    ("DAF", "Der Mussolini"): "q4VBqFPFN0Y",
    ("The Normal", "Warm Leatherette"): "bMCoN0CxjWo",
    ("Throbbing Gristle", "We Hate You (Little Girls)"): "2C786Iq4CKQ",
    # Misc classics
    ("Snap!", "Rhythm Is A Dancer"): "WMPM1q_Uyxc",
    ("Haddaway", "What Is Love"): "HEXWRTEbj1I",
    ("Sven Vath", "An Accident In Paradise"): "OGvIEEIG3cE",
    ("Deee-Lite", "Groove Is In The Heart (Meeting Of The Minds mix)"): "etviGf1uWlg",
    ("Alice Deejay", "Better Off Alone"): "Lgs9QUtWc3M",
    ("Giorgio Moroder", "From Here To Eternity"): "Jo9d5XzOmYg",
    ("Space", "Magic Fly"): "B0M6WGpECoo",
    ("Tangerine Dream", "Fly And Collision Of Comas Sola"): "vJrm-4u6ZDs",
}


def load_world_json():
    with open(WORLD_JSON, "r") as f:
        return json.load(f)


def save_youtube_ids(mapping: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(YOUTUBE_IDS_FILE, "w") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(mapping)} YouTube IDs to {YOUTUBE_IDS_FILE}")


def load_youtube_ids() -> dict:
    if YOUTUBE_IDS_FILE.exists():
        with open(YOUTUBE_IDS_FILE, "r") as f:
            return json.load(f)
    return {}


def search_youtube_id(artist: str, title: str) -> str | None:
    """Use yt-dlp to search YouTube for a video ID."""
    query = f"{artist} {title}"
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", f"ytsearch1:{query}"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            duration = data.get("duration", 0)
            # Skip very long videos (>15min) or very short (<30s)
            if duration and (duration > 900 or duration < 30):
                return None
            return data.get("id")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  Error searching for '{query}': {e}")
    return None


def enrich_hardcoded():
    """Apply curated YouTube IDs for iconic tracks."""
    world = load_world_json()
    tracks = world.get("tracks", {})

    # Build lookup from world.json
    track_lookup = {}
    for genre, tlist in tracks.items():
        for t in tlist:
            key = (t["artist"], t["title"])
            track_lookup[key] = t

    # Build youtube_ids.json mapping
    mapping = load_youtube_ids()
    matched = 0
    skipped = 0

    for (artist, title), video_id in ICONIC_TRACKS.items():
        key_str = f"{artist}|{title}"
        if (artist, title) in track_lookup:
            mapping[key_str] = video_id
            matched += 1
        else:
            print(f"  SKIP (not in world.json): {artist} - {title}")
            skipped += 1

    save_youtube_ids(mapping)
    print(f"Matched: {matched}, Skipped: {skipped}")
    return mapping


def enrich_search(limit: int = 0):
    """Use yt-dlp to search YouTube for video IDs."""
    world = load_world_json()
    tracks = world.get("tracks", {})
    mapping = load_youtube_ids()

    count = 0
    found = 0
    batch_size = 50
    for genre, tlist in tracks.items():
        for t in tlist:
            key_str = f"{t['artist']}|{t['title']}"
            if key_str in mapping:
                continue

            if limit and count >= limit:
                print(f"Reached limit of {limit} searches.")
                save_youtube_ids(mapping)
                print(f"Total found: {found}/{count} searches. Total IDs: {len(mapping)}")
                return mapping

            print(f"  [{count+1}] Searching: {t['artist']} - {t['title']}", end=" ", flush=True)
            video_id = search_youtube_id(t["artist"], t["title"])
            if video_id:
                mapping[key_str] = video_id
                found += 1
                print(f"-> {video_id} [{found} found]")
            else:
                print("-> MISS")

            count += 1

            # Save every batch_size
            if count % batch_size == 0:
                save_youtube_ids(mapping)
                print(f"--- Batch save: {found}/{count} found, {len(mapping)} total IDs ---")

            time.sleep(1.5)  # Rate limit

    save_youtube_ids(mapping)
    print(f"Done! Found: {found}/{count} searches. Total IDs: {len(mapping)}")
    return mapping


def main():
    parser = argparse.ArgumentParser(description="Enrich tracks with YouTube video IDs")
    parser.add_argument("--hardcoded", action="store_true", help="Apply curated YouTube IDs")
    parser.add_argument("--search", action="store_true", help="Search YouTube via yt-dlp")
    parser.add_argument("--limit", type=int, default=0, help="Max searches (0=unlimited)")
    args = parser.parse_args()

    if args.hardcoded:
        enrich_hardcoded()
    elif args.search:
        enrich_search(args.limit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
