#!/usr/bin/env python3
"""
Merge YouTube video IDs into world.json tracks.

Reads youtube_ids.json mapping and adds `youtube` field to matching tracks.

Usage:
    python3 merge_youtube_ids.py [--dry-run]
"""

import argparse
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
WORLD_JSON = SCRIPT_DIR.parent / "web" / "public" / "data" / "world.json"
YOUTUBE_IDS_FILE = DATA_DIR / "youtube_ids.json"


def main():
    parser = argparse.ArgumentParser(description="Merge YouTube IDs into world.json")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    args = parser.parse_args()

    # Load youtube_ids.json
    if not YOUTUBE_IDS_FILE.exists():
        print(f"Error: {YOUTUBE_IDS_FILE} not found. Run enrich_youtube.py first.")
        return

    with open(YOUTUBE_IDS_FILE, "r") as f:
        youtube_ids = json.load(f)

    print(f"Loaded {len(youtube_ids)} YouTube IDs from {YOUTUBE_IDS_FILE}")

    # Load world.json
    with open(WORLD_JSON, "r") as f:
        world = json.load(f)

    tracks = world.get("tracks", {})
    merged = 0
    already_set = 0

    for genre, tlist in tracks.items():
        for track in tlist:
            key = f"{track['artist']}|{track['title']}"
            if key in youtube_ids:
                video_id = youtube_ids[key]
                url = f"https://youtube.com/watch?v={video_id}"

                if track.get("youtube") == url:
                    already_set += 1
                    continue

                if args.dry_run:
                    print(f"  [DRY RUN] {track['artist']} - {track['title']} -> {url}")
                else:
                    track["youtube"] = url
                merged += 1

    print(f"Merged: {merged}, Already set: {already_set}")

    if not args.dry_run and merged > 0:
        with open(WORLD_JSON, "w") as f:
            json.dump(world, f, indent=2, ensure_ascii=False)
        print(f"Updated {WORLD_JSON}")
    elif args.dry_run:
        print("Dry run complete — no files modified.")


if __name__ == "__main__":
    main()
