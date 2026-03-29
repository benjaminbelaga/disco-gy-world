#!/usr/bin/env python3
"""
DiscoWorld Pipeline — Ingest Discogs Releases XML into PostgreSQL
Streaming parser for the 10GB compressed XML dump.
Filters to Electronic genre only for MVP.
"""

import gzip
import sys
import json
import os
from lxml import etree
from tqdm import tqdm

# Configuration
DUMP_PATH = os.path.expanduser("~/repos/discoworld/data/discogs-dump/discogs_20260301_releases.xml.gz")
OUTPUT_DIR = os.path.expanduser("~/repos/discoworld/data/processed")
ELECTRONIC_ONLY = True
MAX_RELEASES = None  # Set to int for testing, None for full run

# Ensure output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)


def parse_release(elem):
    """Parse a single <release> element into a dict."""
    release_id = elem.get("id")

    # Title
    title = elem.findtext("title", "")

    # Artists
    artists = []
    for artist in elem.findall(".//artists/artist"):
        artist_id = artist.findtext("id", "")
        artist_name = artist.findtext("name", "")
        if artist_name:
            artists.append({"id": artist_id, "name": artist_name})

    # Labels
    labels = []
    for label in elem.findall(".//labels/label"):
        label_name = label.get("name", "")
        catno = label.get("catno", "")
        label_id = label.get("id", "")
        if label_name:
            labels.append({"id": label_id, "name": label_name, "catno": catno})

    # Genres and styles
    genres = [g.text for g in elem.findall(".//genres/genre") if g.text]
    styles = [s.text for s in elem.findall(".//styles/style") if s.text]

    # Country and year
    country = elem.findtext("country", "")
    released = elem.findtext("released", "")
    year = ""
    if released:
        year = released[:4] if len(released) >= 4 else released

    # Format
    formats = []
    for fmt in elem.findall(".//formats/format"):
        fmt_name = fmt.get("name", "")
        fmt_qty = fmt.get("qty", "1")
        descriptions = [d.text for d in fmt.findall(".//description") if d.text]
        formats.append({"name": fmt_name, "qty": fmt_qty, "descriptions": descriptions})

    # Master ID
    master_elem = elem.find("master_id")
    master_id = master_elem.text if master_elem is not None else ""
    is_main = master_elem.get("is_main_release", "false") if master_elem is not None else "false"

    # Tracklist
    tracklist = []
    for track in elem.findall(".//tracklist/track"):
        pos = track.findtext("position", "")
        ttl = track.findtext("title", "")
        dur = track.findtext("duration", "")
        if ttl:
            tracklist.append({"position": pos, "title": ttl, "duration": dur})

    # Videos (YouTube links)
    videos = []
    for video in elem.findall(".//videos/video"):
        src = video.get("src", "")
        vtitle = video.findtext("title", "")
        if src:
            videos.append({"url": src, "title": vtitle})

    # Data quality
    data_quality = elem.findtext("data_quality", "")

    return {
        "id": release_id,
        "title": title,
        "artists": artists,
        "labels": labels,
        "genres": genres,
        "styles": styles,
        "country": country,
        "year": year,
        "formats": formats,
        "master_id": master_id,
        "is_main_release": is_main == "true",
        "tracklist": tracklist,
        "videos": videos,
        "data_quality": data_quality,
    }


def is_vinyl(release):
    """Check if release is vinyl format."""
    for fmt in release["formats"]:
        name = fmt["name"].lower()
        descs = [d.lower() for d in fmt.get("descriptions", [])]
        if name == "vinyl" or "12\"" in descs or "10\"" in descs or "7\"" in descs or "lp" in name:
            return True
    return False


def main():
    print(f"Parsing: {DUMP_PATH}")
    print(f"Electronic only: {ELECTRONIC_ONLY}")
    print(f"Output: {OUTPUT_DIR}")

    # Stats
    total = 0
    electronic = 0
    vinyl_count = 0
    with_youtube = 0

    # Output files
    releases_file = open(os.path.join(OUTPUT_DIR, "electronic_releases.jsonl"), "w")

    # Style counter for analysis
    style_counts = {}
    country_counts = {}
    year_counts = {}
    label_counts = {}

    # Streaming parse
    context = etree.iterparse(
        gzip.open(DUMP_PATH, "rb"),
        events=("end",),
        tag="release"
    )

    pbar = tqdm(desc="Parsing releases", unit=" releases")

    for event, elem in context:
        total += 1
        pbar.update(1)

        if MAX_RELEASES and total > MAX_RELEASES:
            break

        release = parse_release(elem)

        # Filter: Electronic genre only
        if ELECTRONIC_ONLY and "Electronic" not in release["genres"]:
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
            continue

        electronic += 1

        # Check if vinyl
        if is_vinyl(release):
            vinyl_count += 1

        # Check YouTube
        if release["videos"]:
            with_youtube += 1

        # Count styles
        for style in release["styles"]:
            style_counts[style] = style_counts.get(style, 0) + 1

        # Count countries
        if release["country"]:
            country_counts[release["country"]] = country_counts.get(release["country"], 0) + 1

        # Count years
        if release["year"] and release["year"].isdigit():
            yr = release["year"]
            year_counts[yr] = year_counts.get(yr, 0) + 1

        # Count labels
        for label in release["labels"]:
            label_counts[label["name"]] = label_counts.get(label["name"], 0) + 1

        # Write to JSONL
        releases_file.write(json.dumps(release) + "\n")

        # Free memory
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

        # Progress every 100K
        if electronic % 100000 == 0:
            pbar.set_postfix({
                "electronic": electronic,
                "vinyl": vinyl_count,
                "youtube": with_youtube,
            })

    pbar.close()
    releases_file.close()

    # Write stats
    stats = {
        "total_releases": total,
        "electronic_releases": electronic,
        "vinyl_releases": vinyl_count,
        "with_youtube": with_youtube,
        "styles": dict(sorted(style_counts.items(), key=lambda x: -x[1])[:100]),
        "countries": dict(sorted(country_counts.items(), key=lambda x: -x[1])[:50]),
        "years": dict(sorted(year_counts.items())),
        "top_labels": dict(sorted(label_counts.items(), key=lambda x: -x[1])[:200]),
    }

    with open(os.path.join(OUTPUT_DIR, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n=== DONE ===")
    print(f"Total releases scanned: {total:,}")
    print(f"Electronic releases: {electronic:,}")
    print(f"Vinyl releases: {vinyl_count:,}")
    print(f"With YouTube links: {with_youtube:,}")
    print(f"Unique styles: {len(style_counts)}")
    print(f"Top 10 styles:")
    for style, count in sorted(style_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {style}: {count:,}")


if __name__ == "__main__":
    main()
