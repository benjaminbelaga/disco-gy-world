"""
Taxonomy Bridge: Maps Discogs 100 styles <-> Ishkur/world.json 166 genres.

Strategy:
1. Load world.json genres (166 genres with name, aka, scene, biome)
2. Load Discogs styles from stats.json (100 electronic styles)
3. Fuzzy match: normalize names, match by substring/alias
4. Manual overrides for ambiguous or non-matching cases
5. Output: bidirectional many-to-many mapping
"""
import json
from pathlib import Path
from difflib import SequenceMatcher

DATA_DIR = Path(__file__).parent / "data"
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Manual overrides for styles that don't fuzzy-match well
# key = Discogs style, value = list of world.json genre names
MANUAL_OVERRIDES = {
    # Discogs styles -> world.json genre names
    "House": ["Chicago House", "UK House", "Anthem House", "Disco House", "Euro Deep House"],
    "Techno": ["Detroit Techno", "Bangin Techno", "Euro Techno"],
    "Acid": ["Acid House", "Hard Acid"],
    "Breaks": ["Breaks", "Chemical Breaks", "Florida Breaks", "Freeland Breaks", "Nu Skool Breaks"],
    "Euro House": ["Eurohouse", "Eurodance"],
    "Leftfield": ["Experimental"],
    "Synth-pop": ["Synthpop"],
    "IDM": ["Braindance"],
    "Abstract": ["Experimental", "Glitch"],
    "Drum n Bass": ["Neurofunk", "Liquid Funk", "Techstep", "Jazzstep", "Darkstep", "Jumpup"],
    "Jungle": ["Atmospheric Jungle", "Ragga Jungle"],
    "Psy-Trance": ["Psychedelic Trance", "Goa Trance", "Full On", "Darkpsy", "Progpsy"],
    "Deep House": ["US Deep House", "Euro Deep House", "Deeptech"],
    "Minimal": ["Minimal Techno", "Minimal Tech", "Microhouse", "Minimal Prog"],
    "Garage House": ["Garage", "Speed Garage", "2-Step Garage"],
    "UK Garage": ["2-Step Garage", "Speed Garage", "Future Garage", "Grime"],
    "Electro House": ["Electrohouse", "Filthy Electrohouse", "Fidget House", "Dutch House"],
    "New Wave": ["Darkwave", "Synthpop"],
    "Pop Rock": [],  # Not electronic — no mapping
    "Alternative Rock": [],  # Not electronic
    "Indie Rock": [],  # Not electronic
    "Indie Pop": [],  # Not electronic
    "Ballad": [],  # Not electronic
    "Soft Rock": [],  # Not electronic
    "Art Rock": [],  # Not electronic
    "Post Rock": [],  # Not electronic
    "Prog Rock": ["Krautrock"],
    "Psychedelic Rock": ["Krautrock"],
    "Post-Punk": ["Darkwave", "Industrial Rock"],
    "Punk": [],  # Not electronic
    "Folk": [],  # Not electronic
    "Chanson": [],  # Not electronic
    "Latin": ["Reggaeton", "Moombahton"],
    "Vocal": ["Vocal Trance"],
    "Tribal": ["Tribal House"],  # Use existing mapping below
    "Tribal House": ["Tribal House", "World House"],
    "Europop": ["Eurodance", "Eurobeat"],
    "Dance-pop": ["Eurodance", "Handsup"],
    "Italodance": ["Italo House", "Nu Italo"],
    "Vaporwave": ["Synthwave"],
    "Harsh Noise Wall": ["Noise"],
    "Power Electronics": ["Noise", "Industrial"],
    "Dungeon Synth": ["Dark Ambient"],
    "RnB/Swing": ["R&B", "New Jack Swing"],
    "Contemporary R&B": ["R&B"],
    "Pop Rap": ["Rap", "Bling"],
    "Hip Hop": ["Rap", "Eastcoast Rap", "Westcoast Rap", "Conscious Rap"],
    "Field Recording": ["Collage", "Musique Concrete"],
    "Lo-Fi": ["Experimental"],
    "Avantgarde": ["Experimental", "Collage"],
    "Berlin-School": ["Moog", "Spacesynth"],
    "Future Jazz": ["Nu Jazz"],
    "Broken Beat": ["Nu Jazz", "Glitch Hop"],
    "Instrumental": [],  # Too generic
    "Chillwave": ["Synthwave", "Downtempo"],
    "Nu-Disco": ["Nu Italo", "Disco House", "French House"],
    "Gabber": ["Hardcore", "Speedcore"],
    "Italo-Disco": ["Italo Disco", "Spacesynth"],
    "Disco": ["Disco House", "Italo Disco", "Nu Italo"],
    "Musique Concrète": ["Musique Concrete", "Collage"],
    "Minimal Techno": ["Minimal Techno", "Minimal Tech"],
    "Acid House": ["Acid House", "Chicago House"],
}


def normalize(name: str) -> str:
    """Normalize a genre/style name for comparison."""
    return (
        name.lower()
        .strip()
        .replace("-", " ")
        .replace("&", "and")
        .replace("è", "e")
        .replace("é", "e")
    )


def load_world_genres() -> list[dict]:
    """Load genres from world.json (primary source, 166 genres)."""
    world_path = PROJECT_ROOT / "packages" / "web" / "public" / "data" / "world.json"
    if world_path.exists():
        with open(world_path) as f:
            data = json.load(f)
        return data.get("genres", [])
    raise FileNotFoundError(f"world.json not found at {world_path}")


def load_discogs_styles() -> list[str]:
    """Load Discogs electronic styles from stats.json (100 styles)."""
    stats_path = PROJECT_ROOT / "data" / "processed" / "stats.json"
    if stats_path.exists():
        with open(stats_path) as f:
            stats = json.load(f)
        return list(stats.get("styles", {}).keys())
    raise FileNotFoundError(f"stats.json not found at {stats_path}")


def fuzzy_match(style: str, genres: list[dict], threshold: float = 0.75) -> list[str]:
    """Find matching world.json genres for a Discogs style using fuzzy matching."""
    norm_style = normalize(style)
    matches = []

    for genre in genres:
        name = genre.get("name", "")
        norm_name = normalize(name)

        # Exact match
        if norm_style == norm_name:
            matches.append(name)
            continue

        # Check aliases (aka field)
        aka = genre.get("aka", "")
        if aka:
            for alias in aka.split(","):
                alias_norm = normalize(alias.strip())
                if alias_norm == norm_style:
                    matches.append(name)
                    break
                # Also check if style is contained in alias
                if len(norm_style) >= 4 and norm_style in alias_norm:
                    matches.append(name)
                    break

        # Substring match (only for longer names to avoid false positives)
        if len(norm_style) >= 5:
            if norm_style in norm_name or norm_name in norm_style:
                if name not in matches:
                    matches.append(name)

        # Sequence matcher for close but not exact matches
        ratio = SequenceMatcher(None, norm_style, norm_name).ratio()
        if ratio >= threshold and name not in matches:
            matches.append(name)

    return list(set(matches))


def build_bridge() -> dict:
    """Build the bidirectional taxonomy bridge."""
    genres = load_world_genres()
    styles = load_discogs_styles()

    style_to_genres: dict[str, list[str]] = {}
    genre_to_styles: dict[str, list[str]] = {}

    for style in styles:
        # Check manual overrides first
        if style in MANUAL_OVERRIDES:
            mapped = MANUAL_OVERRIDES[style]
            style_to_genres[style] = mapped
        else:
            matched = fuzzy_match(style, genres)
            style_to_genres[style] = matched if matched else []

    # Build reverse mapping
    for style, genre_list in style_to_genres.items():
        for genre in genre_list:
            if genre not in genre_to_styles:
                genre_to_styles[genre] = []
            if style not in genre_to_styles[genre]:
                genre_to_styles[genre].append(style)

    genre_names = [g.get("name", "") for g in genres]

    return {
        "discogs_styles": styles,
        "world_genres": genre_names,
        "style_to_genres": style_to_genres,
        "genre_to_styles": genre_to_styles,
    }


def get_genres_for_style(bridge: dict, style: str) -> list[str]:
    """Get world.json genres mapped to a Discogs style."""
    return bridge["style_to_genres"].get(style, [])


def get_styles_for_genre(bridge: dict, genre: str) -> list[str]:
    """Get Discogs styles mapped to a world.json genre."""
    return bridge["genre_to_styles"].get(genre, [])


def save_bridge(output_path: Path | None = None):
    """Build and save the taxonomy bridge to JSON."""
    bridge = build_bridge()
    path = output_path or PROJECT_ROOT / "data" / "taxonomy_bridge.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(bridge, f, indent=2)

    mapped = sum(1 for s, g in bridge["style_to_genres"].items() if g)
    total = len(bridge["style_to_genres"])
    print(f"Taxonomy bridge saved: {mapped}/{total} styles mapped to genres")
    return bridge


if __name__ == "__main__":
    save_bridge()
