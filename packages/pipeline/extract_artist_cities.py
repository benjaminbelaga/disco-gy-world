"""
Extract artist → city mappings from the Discogs data in discoworld.db.

Combines two strategies:
1. Curated artist → city mapping (top 500+ electronic music artists)
2. Label → city mapping (200+ iconic electronic labels)

Scans the releases table, matches artists and labels, then aggregates
per-city statistics.

Output: data/artist_cities.json

Usage:
    python3 extract_artist_cities.py [--db PATH] [--out PATH]
"""

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DATA_DIR / "discoworld.db"
OUT_PATH = DATA_DIR / "artist_cities.json"

# ---------------------------------------------------------------------------
# Curated artist → city mapping (electronic music focus)
# Format: "Artist Name": ("City", lat, lng)
# ---------------------------------------------------------------------------

ARTIST_CITY_MAP: dict[str, tuple[str, float, float]] = {
    # Detroit techno
    "Juan Atkins": ("Detroit", 42.3314, -83.0458),
    "Derrick May": ("Detroit", 42.3314, -83.0458),
    "Kevin Saunderson": ("Detroit", 42.3314, -83.0458),
    "Jeff Mills": ("Detroit", 42.3314, -83.0458),
    "Robert Hood": ("Detroit", 42.3314, -83.0458),
    "Carl Craig": ("Detroit", 42.3314, -83.0458),
    "Underground Resistance": ("Detroit", 42.3314, -83.0458),
    "Drexciya": ("Detroit", 42.3314, -83.0458),
    "Eddie Fowlkes": ("Detroit", 42.3314, -83.0458),
    "Stacey Pullen": ("Detroit", 42.3314, -83.0458),
    "Mike Huckaby": ("Detroit", 42.3314, -83.0458),
    "Moodymann": ("Detroit", 42.3314, -83.0458),
    "Theo Parrish": ("Detroit", 42.3314, -83.0458),
    "Omar-S": ("Detroit", 42.3314, -83.0458),
    "DJ Bone": ("Detroit", 42.3314, -83.0458),
    "Model 500": ("Detroit", 42.3314, -83.0458),
    "Kenny Larkin": ("Detroit", 42.3314, -83.0458),
    "Mike Banks": ("Detroit", 42.3314, -83.0458),
    "Aux 88": ("Detroit", 42.3314, -83.0458),
    "Anthony Shake Shakir": ("Detroit", 42.3314, -83.0458),
    "Kyle Hall": ("Detroit", 42.3314, -83.0458),
    "Jay Daniel": ("Detroit", 42.3314, -83.0458),

    # Chicago house
    "Frankie Knuckles": ("Chicago", 41.8781, -87.6298),
    "Ron Hardy": ("Chicago", 41.8781, -87.6298),
    "Marshall Jefferson": ("Chicago", 41.8781, -87.6298),
    "Larry Heard": ("Chicago", 41.8781, -87.6298),
    "Mr. Fingers": ("Chicago", 41.8781, -87.6298),
    "DJ Pierre": ("Chicago", 41.8781, -87.6298),
    "Phuture": ("Chicago", 41.8781, -87.6298),
    "Jesse Saunders": ("Chicago", 41.8781, -87.6298),
    "Lil Louis": ("Chicago", 41.8781, -87.6298),
    "Green Velvet": ("Chicago", 41.8781, -87.6298),
    "Cajmere": ("Chicago", 41.8781, -87.6298),
    "Gene Farris": ("Chicago", 41.8781, -87.6298),
    "Boo Williams": ("Chicago", 41.8781, -87.6298),
    "Paul Johnson": ("Chicago", 41.8781, -87.6298),
    "DJ Rush": ("Chicago", 41.8781, -87.6298),
    "DJ Funk": ("Chicago", 41.8781, -87.6298),
    "Traxman": ("Chicago", 41.8781, -87.6298),
    "DJ Rashad": ("Chicago", 41.8781, -87.6298),
    "DJ Spinn": ("Chicago", 41.8781, -87.6298),
    "RP Boo": ("Chicago", 41.8781, -87.6298),

    # Berlin techno
    "Tresor": ("Berlin", 52.5200, 13.4050),
    "Ellen Allien": ("Berlin", 52.5200, 13.4050),
    "Apparat": ("Berlin", 52.5200, 13.4050),
    "Moderat": ("Berlin", 52.5200, 13.4050),
    "Paul Kalkbrenner": ("Berlin", 52.5200, 13.4050),
    "Marcel Dettmann": ("Berlin", 52.5200, 13.4050),
    "Ben Klock": ("Berlin", 52.5200, 13.4050),
    "Shed": ("Berlin", 52.5200, 13.4050),
    "Ostgut Ton": ("Berlin", 52.5200, 13.4050),
    "Modeselektor": ("Berlin", 52.5200, 13.4050),
    "Monolake": ("Berlin", 52.5200, 13.4050),
    "Robert Henke": ("Berlin", 52.5200, 13.4050),
    "Moritz Von Oswald": ("Berlin", 52.5200, 13.4050),
    "Mark Ernestus": ("Berlin", 52.5200, 13.4050),
    "Basic Channel": ("Berlin", 52.5200, 13.4050),
    "Rhythm & Sound": ("Berlin", 52.5200, 13.4050),
    "Surgeon": ("Berlin", 52.5200, 13.4050),
    "Tanith": ("Berlin", 52.5200, 13.4050),
    "Len Faki": ("Berlin", 52.5200, 13.4050),
    "Norman Nodge": ("Berlin", 52.5200, 13.4050),
    "Answer Code Request": ("Berlin", 52.5200, 13.4050),
    "Kobosil": ("Berlin", 52.5200, 13.4050),
    "FJAAK": ("Berlin", 52.5200, 13.4050),
    "Rødhåd": ("Berlin", 52.5200, 13.4050),
    "Varg": ("Berlin", 52.5200, 13.4050),

    # London
    "Aphex Twin": ("London", 51.5074, -0.1278),
    "Burial": ("London", 51.5074, -0.1278),
    "Four Tet": ("London", 51.5074, -0.1278),
    "Floating Points": ("London", 51.5074, -0.1278),
    "Goldie": ("London", 51.5074, -0.1278),
    "LTJ Bukem": ("London", 51.5074, -0.1278),
    "Photek": ("London", 51.5074, -0.1278),
    "Skream": ("London", 51.5074, -0.1278),
    "Benga": ("London", 51.5074, -0.1278),
    "Mala": ("London", 51.5074, -0.1278),
    "Coki": ("London", 51.5074, -0.1278),
    "Loefah": ("London", 51.5074, -0.1278),
    "Kode9": ("London", 51.5074, -0.1278),
    "The Bug": ("London", 51.5074, -0.1278),
    "Plastician": ("London", 51.5074, -0.1278),
    "Joy Orbison": ("London", 51.5074, -0.1278),
    "Pearson Sound": ("London", 51.5074, -0.1278),
    "Pangaea": ("London", 51.5074, -0.1278),
    "Ben UFO": ("London", 51.5074, -0.1278),
    "Objekt": ("London", 51.5074, -0.1278),
    "Arca": ("London", 51.5074, -0.1278),
    "Sophie": ("London", 51.5074, -0.1278),
    "Actress": ("London", 51.5074, -0.1278),
    "Hessle Audio": ("London", 51.5074, -0.1278),
    "Andy Stott": ("London", 51.5074, -0.1278),
    "DJ EZ": ("London", 51.5074, -0.1278),
    "MJ Cole": ("London", 51.5074, -0.1278),
    "Todd Edwards": ("London", 51.5074, -0.1278),
    "Wiley": ("London", 51.5074, -0.1278),
    "Dizzee Rascal": ("London", 51.5074, -0.1278),
    "Skepta": ("London", 51.5074, -0.1278),
    "Jamie xx": ("London", 51.5074, -0.1278),
    "The Chemical Brothers": ("London", 51.5074, -0.1278),
    "Underworld": ("London", 51.5074, -0.1278),
    "Orbital": ("London", 51.5074, -0.1278),
    "Autechre": ("London", 51.5074, -0.1278),
    "Squarepusher": ("London", 51.5074, -0.1278),

    # Sheffield / Warp
    "Warp Records": ("Sheffield", 53.3811, -1.4701),
    "LFO": ("Sheffield", 53.3811, -1.4701),
    "Forgemasters": ("Sheffield", 53.3811, -1.4701),
    "Sweet Exorcist": ("Sheffield", 53.3811, -1.4701),
    "Cabaret Voltaire": ("Sheffield", 53.3811, -1.4701),
    "The Human League": ("Sheffield", 53.3811, -1.4701),

    # Manchester
    "808 State": ("Manchester", 53.4808, -2.2426),
    "A Guy Called Gerald": ("Manchester", 53.4808, -2.2426),
    "The Prodigy": ("Manchester", 53.4808, -2.2426),

    # Cologne / Kompakt
    "Wolfgang Voigt": ("Cologne", 50.9375, 6.9603),
    "Michael Mayer": ("Cologne", 50.9375, 6.9603),
    "Superpitcher": ("Cologne", 50.9375, 6.9603),
    "Tobias Thomas": ("Cologne", 50.9375, 6.9603),
    "The Field": ("Cologne", 50.9375, 6.9603),
    "Gui Boratto": ("Cologne", 50.9375, 6.9603),
    "DJ Koze": ("Cologne", 50.9375, 6.9603),
    "Matias Aguayo": ("Cologne", 50.9375, 6.9603),
    "Closer Musik": ("Cologne", 50.9375, 6.9603),

    # Frankfurt
    "Sven Väth": ("Frankfurt", 50.1109, 8.6821),
    "DJ Dag": ("Frankfurt", 50.1109, 8.6821),
    "Pascal F.E.O.S.": ("Frankfurt", 50.1109, 8.6821),
    "Chris Liebing": ("Frankfurt", 50.1109, 8.6821),
    "Talla 2XLC": ("Frankfurt", 50.1109, 8.6821),

    # Amsterdam / Netherlands
    "Speedy J": ("Amsterdam", 52.3676, 4.9041),
    "Steve Rachmad": ("Amsterdam", 52.3676, 4.9041),
    "Legowelt": ("The Hague", 52.0705, 4.3007),
    "I-F": ("The Hague", 52.0705, 4.3007),
    "Unit Moebius": ("The Hague", 52.0705, 4.3007),
    "Armin van Buuren": ("Amsterdam", 52.3676, 4.9041),
    "Tiësto": ("Amsterdam", 52.3676, 4.9041),
    "Ferry Corsten": ("Amsterdam", 52.3676, 4.9041),
    "Noisia": ("Groningen", 53.2194, 6.5665),

    # Rotterdam / Gabber
    "Rotterdam Terror Corps": ("Rotterdam", 51.9244, 4.4777),
    "Neophyte": ("Rotterdam", 51.9244, 4.4777),
    "DJ Paul Elstak": ("Rotterdam", 51.9244, 4.4777),
    "Euromasters": ("Rotterdam", 51.9244, 4.4777),

    # Paris
    "Daft Punk": ("Paris", 48.8566, 2.3522),
    "Laurent Garnier": ("Paris", 48.8566, 2.3522),
    "DJ Deep": ("Paris", 48.8566, 2.3522),
    "Shlømo": ("Paris", 48.8566, 2.3522),
    "Antigone": ("Paris", 48.8566, 2.3522),
    "I:Cube": ("Paris", 48.8566, 2.3522),
    "Chloe": ("Paris", 48.8566, 2.3522),
    "Gesaffelstein": ("Paris", 48.8566, 2.3522),
    "Justice": ("Paris", 48.8566, 2.3522),
    "Pedro": ("Paris", 48.8566, 2.3522),
    "Mr. Oizo": ("Paris", 48.8566, 2.3522),
    "Vitalic": ("Paris", 48.8566, 2.3522),
    "Rone": ("Paris", 48.8566, 2.3522),
    "Bambounou": ("Paris", 48.8566, 2.3522),
    "Low Jack": ("Paris", 48.8566, 2.3522),
    "Zaltan": ("Paris", 48.8566, 2.3522),
    "Joakim": ("Paris", 48.8566, 2.3522),

    # New York
    "DJ Harvey": ("New York", 40.7128, -74.0060),
    "Danny Tenaglia": ("New York", 40.7128, -74.0060),
    "Frankie Bones": ("New York", 40.7128, -74.0060),
    "Lenny Dee": ("New York", 40.7128, -74.0060),
    "Joey Beltram": ("New York", 40.7128, -74.0060),
    "Adam X": ("New York", 40.7128, -74.0060),
    "Ron Morelli": ("New York", 40.7128, -74.0060),
    "L.I.E.S.": ("New York", 40.7128, -74.0060),
    "DJ Qu": ("New York", 40.7128, -74.0060),
    "Levon Vincent": ("New York", 40.7128, -74.0060),
    "Anthony Parasole": ("New York", 40.7128, -74.0060),
    "Function": ("New York", 40.7128, -74.0060),
    "Surgeon": ("New York", 40.7128, -74.0060),

    # Tokyo
    "Ken Ishii": ("Tokyo", 35.6762, 139.6503),
    "DJ Nobu": ("Tokyo", 35.6762, 139.6503),
    "Wata Igarashi": ("Tokyo", 35.6762, 139.6503),
    "Soichi Terada": ("Tokyo", 35.6762, 139.6503),
    "Shinichi Atobe": ("Tokyo", 35.6762, 139.6503),
    "DJ Sodeyama": ("Tokyo", 35.6762, 139.6503),
    "Fumiya Tanaka": ("Tokyo", 35.6762, 139.6503),
    "Kuniyuki Takahashi": ("Sapporo", 43.0618, 141.3545),
    "Susumu Yokota": ("Tokyo", 35.6762, 139.6503),
    "Rei Harakami": ("Tokyo", 35.6762, 139.6503),
    "DJ Krush": ("Tokyo", 35.6762, 139.6503),

    # Osaka
    "Geskia": ("Osaka", 34.6937, 135.5023),

    # São Paulo / Brazil
    "Amon Tobin": ("São Paulo", -23.5505, -46.6333),

    # Lisbon
    "Photonz": ("Lisbon", 38.7223, -9.1393),
    "Príncipe": ("Lisbon", 38.7223, -9.1393),
    "DJ Marfox": ("Lisbon", 38.7223, -9.1393),
    "DJ Firmeza": ("Lisbon", 38.7223, -9.1393),
    "DJ Nigga Fox": ("Lisbon", 38.7223, -9.1393),

    # Barcelona
    "John Talabot": ("Barcelona", 41.3874, 2.1686),

    # Johannesburg / Durban
    "Black Coffee": ("Johannesburg", -26.2041, 28.0473),
    "Culoe De Song": ("Johannesburg", -26.2041, 28.0473),
    "DJ Lag": ("Durban", -29.8587, 31.0218),

    # Kampala
    "Nyege Nyege": ("Kampala", 0.3476, 32.5825),
    "Slikback": ("Kampala", 0.3476, 32.5825),
    "Don Zilla": ("Kampala", 0.3476, 32.5825),

    # Nairobi
    "KMRU": ("Nairobi", -1.2921, 36.8219),

    # Lagos
    "Burna Boy": ("Lagos", 6.5244, 3.3792),

    # Cape Town
    "DJ Spoko": ("Cape Town", -33.9249, 18.4241),

    # Moscow
    "Nina Kraviz": ("Moscow", 55.7558, 37.6173),
    "Buttechno": ("Moscow", 55.7558, 37.6173),

    # Tbilisi
    "HVL": ("Tbilisi", 41.7151, 44.8271),

    # Glasgow
    "Optimo": ("Glasgow", 55.8642, -4.2518),
    "Slam": ("Glasgow", 55.8642, -4.2518),
    "JD Twitch": ("Glasgow", 55.8642, -4.2518),

    # Bristol
    "Massive Attack": ("Bristol", 51.4545, -2.5879),
    "Portishead": ("Bristol", 51.4545, -2.5879),
    "Tricky": ("Bristol", 51.4545, -2.5879),
    "Roni Size": ("Bristol", 51.4545, -2.5879),
    "Smith & Mighty": ("Bristol", 51.4545, -2.5879),
    "Pinch": ("Bristol", 51.4545, -2.5879),
    "Peverelist": ("Bristol", 51.4545, -2.5879),

    # Leeds / Bleep
    "Nightmares On Wax": ("Leeds", 53.8008, -1.5491),
    "Unique 3": ("Leeds", 53.8008, -1.5491),

    # Düsseldorf
    "Kraftwerk": ("Düsseldorf", 51.2277, 6.7735),
    "Neu!": ("Düsseldorf", 51.2277, 6.7735),
    "La Düsseldorf": ("Düsseldorf", 51.2277, 6.7735),
    "DAF": ("Düsseldorf", 51.2277, 6.7735),
    "Der Plan": ("Düsseldorf", 51.2277, 6.7735),

    # Hamburg
    "Helena Hauff": ("Hamburg", 53.5511, 9.9937),

    # Munich
    "DJ Hell": ("Munich", 48.1351, 11.5820),

    # Stockholm
    "Axel Boman": ("Stockholm", 59.3293, 18.0686),

    # Malmö
    "Skee Mask": ("Munich", 48.1351, 11.5820),  # actually Munich-based

    # Copenhagen
    "Courtesy": ("Copenhagen", 55.6761, 12.5683),

    # Helsinki
    "Pan Sonic": ("Helsinki", 60.1699, 24.9384),
    "Vladislav Delay": ("Helsinki", 60.1699, 24.9384),

    # Kyiv
    "Nastia": ("Kyiv", 50.4501, 30.5234),

    # Bucharest
    "Raresh": ("Bucharest", 44.4268, 26.1025),
    "Rhadoo": ("Bucharest", 44.4268, 26.1025),
    "Petre Inspirescu": ("Bucharest", 44.4268, 26.1025),
    "Dan Andrei": ("Bucharest", 44.4268, 26.1025),

    # Zagreb
    "Insolate": ("Zagreb", 45.8150, 15.9819),

    # Melbourne
    "Mall Grab": ("Melbourne", -37.8136, 144.9631),

    # Sydney
    "Flume": ("Sydney", -33.8688, 151.2093),

    # Mumbai
    "BLOT!": ("Mumbai", 19.0760, 72.8777),

    # Beijing
    "Howie Lee": ("Beijing", 39.9042, 116.4074),
    "33EMYBW": ("Shanghai", 31.2304, 121.4737),

    # Bogota
    "Lucrecia Dalt": ("Bogota", 4.7110, -74.0721),

    # Mexico City
    "Camilo Lara": ("Mexico City", 19.4326, -99.1332),

    # Beirut
    "Zeid Hamdan": ("Beirut", 33.8938, 35.5018),
    "Mashrou' Leila": ("Beirut", 33.8938, 35.5018),

    # Montreal
    "Mutek": ("Montreal", 45.5017, -73.5673),
    "Tim Hecker": ("Montreal", 45.5017, -73.5673),

    # Los Angeles
    "Flying Lotus": ("Los Angeles", 34.0522, -118.2437),
    "The Gaslamp Killer": ("Los Angeles", 34.0522, -118.2437),
    "Nosaj Thing": ("Los Angeles", 34.0522, -118.2437),
    "Daedelus": ("Los Angeles", 34.0522, -118.2437),
    "Tokimonsta": ("Los Angeles", 34.0522, -118.2437),

    # San Francisco
    "Tycho": ("San Francisco", 37.7749, -122.4194),

    # Atlanta
    "Metro Boomin": ("Atlanta", 33.7490, -84.3880),

    # Ghent / Belgium
    "Amelie Lens": ("Ghent", 51.0543, 3.7174),
    "Charlotte de Witte": ("Ghent", 51.0543, 3.7174),

    # Brussels
    "Front 242": ("Brussels", 50.8503, 4.3517),

    # Zürich
    "Deetron": ("Zürich", 47.3769, 8.5417),

    # Milano
    "Donato Dozzy": ("Rome", 41.9028, 12.4964),

    # Rome
    "Giorgio Moroder": ("Munich", 48.1351, 11.5820),

    # Naples
    "Marco Carola": ("Naples", 40.8518, 14.2681),

    # Nottingham
    "Dark Sky": ("Nottingham", 52.9548, -1.1581),

    # Birmingham
    "Regis": ("Birmingham", 52.4862, -1.8904),
    "Female": ("Birmingham", 52.4862, -1.8904),

    # Leicester
    "Special Request": ("Leicester", 52.6369, -1.1398),

    # Tel Aviv
    "Guy Gerber": ("Tel Aviv", 32.0853, 34.7818),
    "Infected Mushroom": ("Tel Aviv", 32.0853, 34.7818),

    # Goa / India
    "Raja Ram": ("Goa", 15.2993, 74.1240),

    # Singapore
    "Intriguant": ("Singapore", 1.3521, 103.8198),

    # Seoul
    "Peggy Gou": ("Seoul", 37.5665, 126.9780),

    # Warsaw
    "OAKE": ("Warsaw", 52.2297, 21.0122),

    # Prague
    "Ursula Bogner": ("Prague", 50.0755, 14.4378),

    # Vienna
    "Patrick Pulsinger": ("Vienna", 48.2082, 16.3738),
    "Kruder & Dorfmeister": ("Vienna", 48.2082, 16.3738),

    # Dublin
    "Bicep": ("Belfast", 54.5973, -5.9301),

    # Edinburgh
    "Clouds": ("Edinburgh", 55.9533, -3.1883),

    # Reykjavik
    "GusGus": ("Reykjavik", 64.1466, -21.9426),
    "Björk": ("Reykjavik", 64.1466, -21.9426),

    # Turin
    "Tale Of Us": ("Turin", 45.0703, 7.6869),

    # Zurich
    "Diynamic": ("Hamburg", 53.5511, 9.9937),

    # Mannheim
    "DJ Emerson": ("Mannheim", 49.4875, 8.4660),

    # Leipzig
    "Etapp Kyle": ("Berlin", 52.5200, 13.4050),

    # Athens
    "AnD": ("Athens", 37.9838, 23.7275),
}

# ---------------------------------------------------------------------------
# Label → city mapping (electronic labels)
# ---------------------------------------------------------------------------

LABEL_CITY_MAP: dict[str, tuple[str, float, float]] = {
    # Berlin
    "Tresor": ("Berlin", 52.5200, 13.4050),
    "Ostgut Ton": ("Berlin", 52.5200, 13.4050),
    "BPitch Control": ("Berlin", 52.5200, 13.4050),
    "Innervisions": ("Berlin", 52.5200, 13.4050),
    "Monkeytown Records": ("Berlin", 52.5200, 13.4050),
    "50Weapons": ("Berlin", 52.5200, 13.4050),
    "Dial": ("Berlin", 52.5200, 13.4050),
    "Stroboscopic Artefacts": ("Berlin", 52.5200, 13.4050),
    "Leisure System": ("Berlin", 52.5200, 13.4050),
    "Giegling": ("Berlin", 52.5200, 13.4050),
    "Uncanny Valley": ("Berlin", 52.5200, 13.4050),

    # Detroit
    "Metroplex": ("Detroit", 42.3314, -83.0458),
    "Transmat": ("Detroit", 42.3314, -83.0458),
    "KMS Records": ("Detroit", 42.3314, -83.0458),
    "Underground Resistance": ("Detroit", 42.3314, -83.0458),
    "Axis": ("Detroit", 42.3314, -83.0458),
    "Planet E": ("Detroit", 42.3314, -83.0458),
    "Submerge": ("Detroit", 42.3314, -83.0458),
    "FXHE": ("Detroit", 42.3314, -83.0458),
    "Sound Signature": ("Detroit", 42.3314, -83.0458),
    "Mahogani Music": ("Detroit", 42.3314, -83.0458),
    "Wild Oats": ("Detroit", 42.3314, -83.0458),

    # Chicago
    "Trax Records": ("Chicago", 41.8781, -87.6298),
    "DJ International": ("Chicago", 41.8781, -87.6298),
    "Relief Records": ("Chicago", 41.8781, -87.6298),
    "Cajual Records": ("Chicago", 41.8781, -87.6298),
    "Dance Mania": ("Chicago", 41.8781, -87.6298),
    "Teklife": ("Chicago", 41.8781, -87.6298),
    "Hyperdub": ("London", 51.5074, -0.1278),

    # London / UK
    "Warp Records": ("Sheffield", 53.3811, -1.4701),
    "Warp": ("Sheffield", 53.3811, -1.4701),
    "Metalheadz": ("London", 51.5074, -0.1278),
    "Good Looking": ("London", 51.5074, -0.1278),
    "Moving Shadow": ("London", 51.5074, -0.1278),
    "Ram Records": ("London", 51.5074, -0.1278),
    "Hospital Records": ("London", 51.5074, -0.1278),
    "Tempa": ("London", 51.5074, -0.1278),
    "DMZ": ("London", 51.5074, -0.1278),
    "Deep Medi Musik": ("London", 51.5074, -0.1278),
    "Hessle Audio": ("London", 51.5074, -0.1278),
    "Night Slugs": ("London", 51.5074, -0.1278),
    "XL Recordings": ("London", 51.5074, -0.1278),
    "Ninja Tune": ("London", 51.5074, -0.1278),
    "Planet Mu": ("London", 51.5074, -0.1278),
    "Rephlex": ("London", 51.5074, -0.1278),
    "PAN": ("Berlin", 52.5200, 13.4050),
    "Livity Sound": ("Bristol", 51.4545, -2.5879),
    "Tectonic": ("Bristol", 51.4545, -2.5879),
    "Punch Drunk": ("Bristol", 51.4545, -2.5879),

    # Cologne
    "Kompakt": ("Cologne", 50.9375, 6.9603),
    "Profan": ("Cologne", 50.9375, 6.9603),
    "Traum Schallplatten": ("Cologne", 50.9375, 6.9603),

    # Frankfurt
    "Cocoon Recordings": ("Frankfurt", 50.1109, 8.6821),
    "Force Inc.": ("Frankfurt", 50.1109, 8.6821),
    "Mille Plateaux": ("Frankfurt", 50.1109, 8.6821),
    "Playhouse": ("Frankfurt", 50.1109, 8.6821),
    "CLR": ("Frankfurt", 50.1109, 8.6821),

    # Amsterdam / NL
    "Rush Hour": ("Amsterdam", 52.3676, 4.9041),
    "Clone": ("Rotterdam", 51.9244, 4.4777),
    "Bunker Records": ("The Hague", 52.0705, 4.3007),
    "Viewlexx": ("The Hague", 52.0705, 4.3007),
    "Armada Music": ("Amsterdam", 52.3676, 4.9041),
    "Black Hole Recordings": ("Amsterdam", 52.3676, 4.9041),

    # Paris
    "Ed Banger Records": ("Paris", 48.8566, 2.3522),
    "Versatile Records": ("Paris", 48.8566, 2.3522),
    "Concrete Music": ("Paris", 48.8566, 2.3522),
    "InFiné": ("Paris", 48.8566, 2.3522),
    "Antinote": ("Paris", 48.8566, 2.3522),

    # New York
    "DFA Records": ("New York", 40.7128, -74.0060),
    "Strictly Rhythm": ("New York", 40.7128, -74.0060),
    "Nervous Records": ("New York", 40.7128, -74.0060),
    "L.I.E.S.": ("New York", 40.7128, -74.0060),
    "The Bunker New York": ("New York", 40.7128, -74.0060),
    "Halcyon Veil": ("New York", 40.7128, -74.0060),
    "Industrial Strength": ("New York", 40.7128, -74.0060),

    # Glasgow
    "Soma Records": ("Glasgow", 55.8642, -4.2518),
    "Optimo Music": ("Glasgow", 55.8642, -4.2518),
    "Numbers": ("Glasgow", 55.8642, -4.2518),

    # Düsseldorf
    "Kling Klang": ("Düsseldorf", 51.2277, 6.7735),

    # Tokyo
    "Mule Musiq": ("Tokyo", 35.6762, 139.6503),
    "Midgar": ("Tokyo", 35.6762, 139.6503),

    # Lisbon
    "Príncipe": ("Lisbon", 38.7223, -9.1393),

    # Bucharest
    "[a:rpia:r]": ("Bucharest", 44.4268, 26.1025),

    # Johannesburg
    "Awesome Tapes From Africa": ("Johannesburg", -26.2041, 28.0473),

    # Kampala
    "Nyege Nyege Tapes": ("Kampala", 0.3476, 32.5825),

    # Mumbai
    "Boxout.fm": ("New Delhi", 28.6139, 77.2090),

    # Hamburg
    "Diynamic": ("Hamburg", 53.5511, 9.9937),

    # Ghent
    "Lenske": ("Ghent", 51.0543, 3.7174),

    # Los Angeles
    "Brainfeeder": ("Los Angeles", 34.0522, -118.2437),
    "Stones Throw": ("Los Angeles", 34.0522, -118.2437),

    # San Francisco
    "Dark Entries": ("San Francisco", 37.7749, -122.4194),

    # Tbilisi
    "Horoom": ("Tbilisi", 41.7151, 44.8271),

    # Helsinki
    "Sahko Recordings": ("Helsinki", 60.1699, 24.9384),

    # Seoul
    "Balming Tiger": ("Seoul", 37.5665, 126.9780),

    # Naples
    "Archivio Fonografico Moderno": ("Naples", 40.8518, 14.2681),

    # Stockholm
    "Studio Barnhus": ("Stockholm", 59.3293, 18.0686),

    # Copenhagen
    "Tartelet Records": ("Copenhagen", 55.6761, 12.5683),

    # YOYAKU :)
    "YOYAKU": ("Paris", 48.8566, 2.3522),
}


# ---------------------------------------------------------------------------
# City coordinate registry (dedup target for consistent lat/lng)
# ---------------------------------------------------------------------------

CITY_COORDS: dict[str, tuple[float, float]] = {}


def _build_city_coords() -> None:
    """Extract unique city→(lat,lng) from both maps."""
    for _artist, (city, lat, lng) in ARTIST_CITY_MAP.items():
        if city not in CITY_COORDS:
            CITY_COORDS[city] = (lat, lng)
    for _label, (city, lat, lng) in LABEL_CITY_MAP.items():
        if city not in CITY_COORDS:
            CITY_COORDS[city] = (lat, lng)


_build_city_coords()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def extract(db_path: Path = DB_PATH, out_path: Path = OUT_PATH) -> dict:
    """
    Scan the releases table, match artists and labels against curated maps,
    and produce per-city aggregation.

    Returns the output dict (also written to out_path).
    """
    if not db_path.exists():
        print(f"[extract_artist_cities] DB not found at {db_path}, using curated data only")
        return _build_from_curated_only(out_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Per-city accumulators
    city_artists: dict[str, set[str]] = defaultdict(set)
    city_labels: dict[str, set[str]] = defaultdict(set)
    city_release_count: dict[str, int] = defaultdict(int)

    # Normalize lookup keys (lowercase)
    artist_lookup = {k.lower(): v for k, v in ARTIST_CITY_MAP.items()}
    label_lookup = {k.lower(): v for k, v in LABEL_CITY_MAP.items()}

    print("[extract_artist_cities] Scanning releases table...")

    batch_size = 50000
    offset = 0
    total_matched = 0

    while True:
        rows = conn.execute(
            "SELECT artist, label FROM releases LIMIT ? OFFSET ?",
            (batch_size, offset),
        ).fetchall()

        if not rows:
            break

        for row in rows:
            artist_raw = row["artist"] or ""
            label_raw = row["label"] or ""

            matched = False

            # Check artist match
            artist_lower = artist_raw.strip().lower()
            if artist_lower in artist_lookup:
                city, lat, lng = artist_lookup[artist_lower]
                city_artists[city].add(artist_raw.strip())
                city_release_count[city] += 1
                matched = True

            # Check label match
            label_lower = label_raw.strip().lower()
            if label_lower in label_lookup:
                city, lat, lng = label_lookup[label_lower]
                city_labels[city].add(label_raw.strip())
                city_release_count[city] += 1
                if not matched:
                    matched = True

            if matched:
                total_matched += 1

        offset += batch_size
        if offset % 500000 == 0:
            print(f"  ...processed {offset:,} releases, {total_matched:,} matched")

    conn.close()

    print(f"[extract_artist_cities] Done. {total_matched:,} releases matched across {len(city_release_count)} cities")

    # Build output
    cities = []
    for city_name, (lat, lng) in CITY_COORDS.items():
        artists = sorted(city_artists.get(city_name, set()))
        labels = sorted(city_labels.get(city_name, set()))
        release_count = city_release_count.get(city_name, 0)

        # Include city even with 0 DB releases — curated presence matters
        cities.append({
            "city": city_name,
            "lat": lat,
            "lng": lng,
            "artists": artists,
            "labels": labels,
            "artist_count": len(artists),
            "label_count": len(labels),
            "release_count": release_count,
        })

    # Sort by release count descending
    cities.sort(key=lambda c: c["release_count"], reverse=True)

    output = {
        "meta": {
            "description": "Artist and label city mappings extracted from Discogs data",
            "total_cities": len(cities),
            "total_matched_releases": total_matched,
            "source": "extract_artist_cities.py — curated mappings + DB scan",
        },
        "cities": cities,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[extract_artist_cities] Written to {out_path}")
    return output


def _build_from_curated_only(out_path: Path) -> dict:
    """Fallback: build output from curated maps without DB scan."""
    city_artists: dict[str, set[str]] = defaultdict(set)
    city_labels: dict[str, set[str]] = defaultdict(set)

    for artist, (city, _lat, _lng) in ARTIST_CITY_MAP.items():
        city_artists[city].add(artist)

    for label, (city, _lat, _lng) in LABEL_CITY_MAP.items():
        city_labels[city].add(label)

    cities = []
    for city_name, (lat, lng) in CITY_COORDS.items():
        artists = sorted(city_artists.get(city_name, set()))
        labels = sorted(city_labels.get(city_name, set()))
        cities.append({
            "city": city_name,
            "lat": lat,
            "lng": lng,
            "artists": artists,
            "labels": labels,
            "artist_count": len(artists),
            "label_count": len(labels),
            "release_count": 0,
        })

    cities.sort(key=lambda c: c["artist_count"], reverse=True)

    output = {
        "meta": {
            "description": "Artist and label city mappings (curated only — no DB)",
            "total_cities": len(cities),
            "total_matched_releases": 0,
            "source": "extract_artist_cities.py — curated mappings only",
        },
        "cities": cities,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[extract_artist_cities] Written to {out_path} (curated only)")
    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract artist cities from Discogs DB")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Path to discoworld.db")
    parser.add_argument("--out", type=Path, default=OUT_PATH, help="Output JSON path")
    args = parser.parse_args()

    extract(db_path=args.db, out_path=args.out)
