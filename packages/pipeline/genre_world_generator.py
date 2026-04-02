#!/usr/bin/env python3
"""
Genre World Generator — DiscoWorld Pipeline

Converts world.json (166 genres, 185 links) into a 2D spatial layout
with Voronoi territories for 3D planet heightmap generation.

Pipeline:
  1. Load world.json with existing x/z positions
  2. Group genres into super-genre clusters (scene/biome)
  3. Force-directed layout refinement using link weights
  4. Voronoi tessellation from genre positions
  5. Assign cell properties (elevation, color, population)
  6. Add simplex noise to cell edges for organic coastlines
  7. Output: JSON with polygon coordinates per genre territory
"""

import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
from noise import snoise2
from scipy.spatial import Voronoi

# --- Constants ---

# Biome-to-elevation mapping (0.0 = sea level, 1.0 = peaks)
BIOME_ELEVATION = {
    "techno-massif": 0.85,
    "industrial-wasteland": 0.75,
    "trance-highlands": 0.80,
    "house-plains": 0.40,
    "garage-district": 0.45,
    "ambient-depths": 0.20,
    "idm-crystalline": 0.65,
    "jungle-canopy": 0.55,
    "disco-riviera": 0.35,
    "dubstep-rift": 0.70,
    "urban-quarter": 0.50,
    "source-monuments": 0.60,
    "unknown": 0.30,
}

# Scene-based BPM approximations for elevation fine-tuning
SCENE_BPM = {
    "Techno": 138, "Tech House": 128, "House": 124, "Garage/Deep House": 122,
    "Trance": 140, "Eurotrance": 142, "Psy Trance": 145, "Progressive": 132,
    "Drum n Bass": 170, "Breakbeat": 135, "Bass": 140, "UK Garage": 130,
    "Hardcore": 175, "Hard Dance": 155, "Industrial/Goth": 130,
    "Ambient": 90, "Chill Out": 100, "Downtempo": 105,
    "Intelligent Dance Music": 120, "Electro": 128, "Acid": 133,
    "Hip Hop": 95, "Urban": 100, "Chiptune": 140,
    "Eurodisco": 120, "Europop": 125, "Eurotrash": 125, "Pioneers": 120,
}

# Force layout parameters
FORCE_ITERATIONS = 120
REPULSION_STRENGTH = 800.0
LINK_STRENGTH = 0.015
DAMPING = 0.92
CENTER_GRAVITY = 0.002
MIN_DISTANCE = 2.0

# Noise parameters for organic edges
NOISE_SCALE = 0.08
NOISE_AMPLITUDE = 1.2
NOISE_OCTAVES = 3

# World bounds
WORLD_RADIUS = 48.0
VORONOI_PADDING = 15.0


def load_world(path: str) -> dict:
    """Load world.json and return parsed data."""
    with open(path) as f:
        return json.load(f)


def build_adjacency(genres: list, links: list) -> dict:
    """Build adjacency map from links. Returns {slug: [(target_slug, weight), ...]}."""
    slug_set = {g["slug"] for g in genres}
    adj = defaultdict(list)
    for link in links:
        src, tgt = link["source"], link["target"]
        if src in slug_set and tgt in slug_set:
            # Weight: older links (smaller year diff) = stronger connection
            weight = 1.0
            if link.get("startYear") and link.get("endYear"):
                span = max(1, link["endYear"] - link["startYear"])
                weight = 1.0 / span
            adj[src].append((tgt, weight))
            adj[tgt].append((src, weight))
    return adj


def force_directed_refine(genres: list, adjacency: dict) -> list:
    """
    Apply force-directed layout refinement to existing positions.
    Uses link weights for attraction, scene clustering for grouping.
    """
    n = len(genres)
    slug_to_idx = {g["slug"]: i for i, g in enumerate(genres)}

    # Initialize positions from existing x/z
    pos = np.array([[g["x"], g["z"]] for g in genres], dtype=np.float64)
    vel = np.zeros_like(pos)

    # Scene centroids for clustering gravity
    scene_groups = defaultdict(list)
    for i, g in enumerate(genres):
        scene_groups[g["scene"]].append(i)

    for iteration in range(FORCE_ITERATIONS):
        forces = np.zeros_like(pos)
        alpha = 1.0 - (iteration / FORCE_ITERATIONS)  # cooling

        # Repulsion (all pairs)
        for i in range(n):
            diff = pos[i] - pos  # (n, 2)
            dist = np.sqrt(np.sum(diff ** 2, axis=1))
            dist = np.maximum(dist, MIN_DISTANCE)
            # Avoid self
            dist[i] = 1.0
            repulse = diff / dist[:, np.newaxis] ** 2 * REPULSION_STRENGTH * alpha
            repulse[i] = 0
            forces[i] += repulse.sum(axis=0)

        # Attraction (linked pairs)
        for slug, neighbors in adjacency.items():
            if slug not in slug_to_idx:
                continue
            i = slug_to_idx[slug]
            for tgt_slug, weight in neighbors:
                if tgt_slug not in slug_to_idx:
                    continue
                j = slug_to_idx[tgt_slug]
                diff = pos[j] - pos[i]
                dist = np.linalg.norm(diff)
                if dist > MIN_DISTANCE:
                    forces[i] += diff * dist * LINK_STRENGTH * weight * alpha

        # Scene clustering gravity (mild pull toward scene centroid)
        for scene, indices in scene_groups.items():
            if len(indices) < 2:
                continue
            centroid = pos[indices].mean(axis=0)
            for idx in indices:
                diff = centroid - pos[idx]
                forces[idx] += diff * 0.003 * alpha

        # Center gravity
        forces -= pos * CENTER_GRAVITY

        # Update
        vel = (vel + forces) * DAMPING
        pos += vel

        # Clamp to world bounds
        dist_from_center = np.linalg.norm(pos, axis=1)
        mask = dist_from_center > WORLD_RADIUS
        if mask.any():
            pos[mask] *= (WORLD_RADIUS / dist_from_center[mask])[:, np.newaxis]

    # Write back
    refined = []
    for i, g in enumerate(genres):
        refined.append({**g, "x": float(pos[i, 0]), "z": float(pos[i, 1])})
    return refined


def compute_voronoi(genres: list) -> tuple:
    """
    Compute bounded Voronoi tessellation.
    Returns (scipy Voronoi object, clipped polygons per genre index).
    """
    points = np.array([[g["x"], g["z"]] for g in genres])

    # Add bounding box points to close outer cells
    pad = WORLD_RADIUS + VORONOI_PADDING
    bbox_points = np.array([
        [-pad, -pad], [pad, -pad], [pad, pad], [-pad, pad],
        [-pad, 0], [pad, 0], [0, -pad], [0, pad],
    ])
    all_points = np.vstack([points, bbox_points])

    vor = Voronoi(all_points)

    # Extract and clip polygons for real genres only
    polygons = []
    for i in range(len(genres)):
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]

        if -1 in region or len(region) == 0:
            # Fallback: generate a small hexagon around the point
            polygons.append(_hexagon(points[i], 3.0))
            continue

        verts = vor.vertices[region]

        # Clip to circular world boundary
        clipped = _clip_to_circle(verts, WORLD_RADIUS + 5.0)
        if len(clipped) < 3:
            polygons.append(_hexagon(points[i], 3.0))
            continue

        polygons.append(clipped)

    return vor, polygons


def _hexagon(center: np.ndarray, radius: float) -> np.ndarray:
    """Generate a regular hexagon."""
    angles = np.linspace(0, 2 * math.pi, 7)[:-1]
    return np.column_stack([
        center[0] + radius * np.cos(angles),
        center[1] + radius * np.sin(angles),
    ])


def _clip_to_circle(vertices: np.ndarray, radius: float) -> np.ndarray:
    """Clip polygon vertices to a circular boundary."""
    center = np.array([0.0, 0.0])
    clipped = []
    n = len(vertices)

    for i in range(n):
        curr = vertices[i]
        next_v = vertices[(i + 1) % n]
        curr_inside = np.linalg.norm(curr - center) <= radius
        next_inside = np.linalg.norm(next_v - center) <= radius

        if curr_inside:
            clipped.append(curr)
        if curr_inside != next_inside:
            # Find intersection with circle
            intersect = _circle_intersect(curr, next_v, radius)
            if intersect is not None:
                clipped.append(intersect)

    return np.array(clipped) if clipped else vertices


def _circle_intersect(p1: np.ndarray, p2: np.ndarray, r: float):
    """Find intersection of line segment p1-p2 with circle of radius r at origin."""
    d = p2 - p1
    a = np.dot(d, d)
    b = 2 * np.dot(p1, d)
    c = np.dot(p1, p1) - r * r
    disc = b * b - 4 * a * c
    if disc < 0:
        return None
    sqrt_disc = math.sqrt(disc)
    for t in [(-b - sqrt_disc) / (2 * a), (-b + sqrt_disc) / (2 * a)]:
        if 0 <= t <= 1:
            return p1 + t * d
    return None


def add_noise_to_edges(polygons: list, seed: int = 42) -> list:
    """Add simplex noise to polygon edges for organic coastlines."""
    noisy_polygons = []
    for poly in polygons:
        if len(poly) < 3:
            noisy_polygons.append(poly)
            continue

        new_verts = []
        n = len(poly)
        for i in range(n):
            curr = poly[i]
            next_v = poly[(i + 1) % n]

            # Add current vertex with noise offset
            noise_val = snoise2(
                curr[0] * NOISE_SCALE + seed,
                curr[1] * NOISE_SCALE + seed,
                octaves=NOISE_OCTAVES,
            )
            offset = noise_val * NOISE_AMPLITUDE
            # Offset perpendicular to edge direction
            edge = next_v - curr
            edge_len = np.linalg.norm(edge)
            if edge_len > 0:
                perp = np.array([-edge[1], edge[0]]) / edge_len
                new_verts.append(curr + perp * offset)
            else:
                new_verts.append(curr)

            # Add midpoint with noise for more organic shape
            if edge_len > 4.0:
                mid = (curr + next_v) / 2
                mid_noise = snoise2(
                    mid[0] * NOISE_SCALE * 1.5 + seed,
                    mid[1] * NOISE_SCALE * 1.5 + seed,
                    octaves=NOISE_OCTAVES,
                )
                if edge_len > 0:
                    new_verts.append(mid + perp * mid_noise * NOISE_AMPLITUDE * 0.7)

        noisy_polygons.append(np.array(new_verts))
    return noisy_polygons


def compute_elevation(genre: dict) -> float:
    """
    Compute elevation for a genre territory.
    Combines biome base elevation + BPM-derived offset + release_count modifier.
    """
    biome = genre.get("biome", "unknown")
    scene = genre.get("scene", "")
    release_count = genre.get("release_count", 0)

    # Base elevation from biome
    base = BIOME_ELEVATION.get(biome, 0.30)

    # BPM offset: higher BPM = slightly higher elevation
    bpm = SCENE_BPM.get(scene, 120)
    bpm_offset = (bpm - 120) / 200.0  # -0.15 to +0.275

    # Release count: popular genres get slight elevation boost
    if release_count > 0:
        pop_offset = min(0.1, math.log10(max(1, release_count)) / 60.0)
    else:
        pop_offset = 0.0

    return max(0.05, min(1.0, base + bpm_offset * 0.3 + pop_offset))


def build_territories(genres: list, polygons: list, biomes: list) -> list:
    """Build the final territory data structure."""
    biome_map = {b["biome"]: b for b in biomes}

    territories = []
    for i, genre in enumerate(genres):
        poly = polygons[i]
        center = np.array([genre["x"], genre["z"]])
        elevation = compute_elevation(genre)

        biome_data = biome_map.get(genre.get("biome", ""), {})
        color = genre.get("color", biome_data.get("color", "#888888"))

        # Compute polygon area for territory size
        area = _polygon_area(poly)

        territory = {
            "slug": genre["slug"],
            "name": genre["name"],
            "scene": genre["scene"],
            "biome": genre.get("biome", "unknown"),
            "center": [round(float(center[0]), 2), round(float(center[1]), 2)],
            "elevation": round(elevation, 3),
            "color": color,
            "release_count": genre.get("release_count", 0),
            "area": round(float(area), 1),
            "polygon": [[round(float(v[0]), 2), round(float(v[1]), 2)] for v in poly],
            "label_offset": [0, 0],  # Can be refined for label placement
        }
        territories.append(territory)

    return territories


def _polygon_area(vertices: np.ndarray) -> float:
    """Compute polygon area using shoelace formula."""
    n = len(vertices)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += vertices[i][0] * vertices[j][1]
        area -= vertices[j][0] * vertices[i][1]
    return abs(area) / 2.0


def generate(world_path: str, output_path: str) -> dict:
    """
    Main pipeline: load world.json -> refine layout -> Voronoi -> territories -> output.
    Returns the generated data dict.
    """
    print("[1/6] Loading world.json...")
    world = load_world(world_path)
    genres = world["genres"]
    links = world["links"]
    biomes = world.get("biomes", [])
    print(f"       {len(genres)} genres, {len(links)} links, {len(biomes)} biomes")

    print("[2/6] Building adjacency graph...")
    adjacency = build_adjacency(genres, links)
    edge_count = sum(len(v) for v in adjacency.values()) // 2
    print(f"       {edge_count} edges in adjacency graph")

    print("[3/6] Force-directed layout refinement...")
    genres = force_directed_refine(genres, adjacency)

    print("[4/6] Computing Voronoi tessellation...")
    vor, polygons = compute_voronoi(genres)
    print(f"       {len(polygons)} cells generated")

    print("[5/6] Adding organic noise to edges...")
    polygons = add_noise_to_edges(polygons)

    print("[6/6] Building territory data...")
    territories = build_territories(genres, polygons, biomes)

    # Build scene clusters for continent info
    scene_clusters = defaultdict(list)
    for t in territories:
        scene_clusters[t["scene"]].append(t["slug"])

    result = {
        "meta": {
            "version": "1.0.0",
            "generator": "genre_world_generator.py",
            "genre_count": len(territories),
            "world_radius": WORLD_RADIUS,
        },
        "territories": territories,
        "continents": {
            scene: {
                "genres": slugs,
                "count": len(slugs),
            }
            for scene, slugs in sorted(scene_clusters.items())
        },
    }

    # Write output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, separators=(",", ":"))

    size_kb = os.path.getsize(output_path) / 1024
    print(f"\nOutput: {output_path} ({size_kb:.1f} KB)")
    return result


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    world_path = os.path.join(base, "..", "web", "public", "data", "world.json")
    output_path = os.path.join(base, "..", "web", "public", "data", "genre_planet.json")

    if len(sys.argv) > 1:
        world_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    generate(world_path, output_path)


if __name__ == "__main__":
    main()
