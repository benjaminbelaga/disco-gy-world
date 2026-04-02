#!/usr/bin/env python3
"""
Heightmap Generator — DiscoWorld Pipeline

Takes Voronoi territories from genre_planet.json and generates:
  1. A 2048x2048 heightmap PNG (grayscale, 16-bit)
  2. A metadata JSON with terrain statistics

Elevation rules:
  - BPM/biome maps to base altitude
  - release_count maps to density/roughness
  - Same-scene territories merge into continent landmasses
  - Ocean fills space between unrelated super-genres
  - Simplex noise adds terrain detail
"""

import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
from noise import snoise2

# --- Constants ---

HEIGHTMAP_SIZE = 2048  # Default; use --size 1024 for faster builds
OCEAN_LEVEL = 0.15       # Below this = ocean (dark)
COAST_BLEND = 0.08       # Smooth transition at coastlines
NOISE_OCTAVES = 6
NOISE_PERSISTENCE = 0.5
NOISE_LACUNARITY = 2.0
NOISE_SCALE = 0.005
DETAIL_NOISE_SCALE = 0.02
ROUGHNESS_SCALE = 0.04


def load_territories(path: str) -> dict:
    """Load genre_planet.json."""
    with open(path) as f:
        return json.load(f)


def point_in_polygon(point: np.ndarray, polygon: np.ndarray) -> bool:
    """Ray casting algorithm for point-in-polygon test."""
    x, y = point
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def build_territory_lookup(territories: list, size: int, world_radius: float) -> np.ndarray:
    """
    Build a 2D grid mapping each pixel to a territory index (-1 = ocean).
    Uses polygon containment test with spatial optimization.
    """
    grid = np.full((size, size), -1, dtype=np.int32)
    scale = size / (2 * world_radius)

    # Pre-convert polygons to numpy arrays and compute bounding boxes
    polys = []
    bboxes = []
    for t in territories:
        poly = np.array(t["polygon"])
        polys.append(poly)
        bboxes.append((poly[:, 0].min(), poly[:, 0].max(),
                        poly[:, 1].min(), poly[:, 1].max()))

    # Convert pixel coords to world coords and test containment
    # Process in blocks for efficiency
    block_size = 32
    for by in range(0, size, block_size):
        for bx in range(0, size, block_size):
            # Block center in world coords
            cx = (bx + block_size / 2) / scale - world_radius
            cy = (by + block_size / 2) / scale - world_radius
            block_radius = (block_size / scale) * 1.5

            # Find candidate territories for this block
            candidates = []
            for idx, (xmin, xmax, ymin, ymax) in enumerate(bboxes):
                if (xmin - block_radius <= cx <= xmax + block_radius and
                        ymin - block_radius <= cy <= ymax + block_radius):
                    candidates.append(idx)

            if not candidates:
                continue

            for py in range(by, min(by + block_size, size)):
                for px in range(bx, min(bx + block_size, size)):
                    wx = px / scale - world_radius
                    wy = py / scale - world_radius
                    point = np.array([wx, wy])

                    for idx in candidates:
                        xmin, xmax, ymin, ymax = bboxes[idx]
                        if xmin <= wx <= xmax and ymin <= wy <= ymax:
                            if point_in_polygon(point, polys[idx]):
                                grid[py, px] = idx
                                break

    return grid


def build_distance_field(grid: np.ndarray, iterations: int = 8) -> np.ndarray:
    """
    Build approximate distance field from territory edges.
    Positive = inside territory, negative = ocean.
    Used for smooth coastline blending.
    """
    land = (grid >= 0).astype(np.float32)

    # Simple blur to create distance approximation
    from scipy.ndimage import gaussian_filter
    distance = gaussian_filter(land, sigma=iterations)
    return distance


def generate_heightmap(data: dict, output_png: str, output_meta: str, size: int = None):
    """
    Main heightmap generation pipeline.
    """
    territories = data["territories"]
    world_radius = data["meta"]["world_radius"]
    if size is None:
        size = HEIGHTMAP_SIZE

    print(f"[1/5] Building territory lookup grid ({size}x{size})...")
    grid = build_territory_lookup(territories, size, world_radius)

    land_pixels = np.sum(grid >= 0)
    total_pixels = size * size
    print(f"       Land coverage: {land_pixels / total_pixels * 100:.1f}%")

    print("[2/5] Computing distance field for coastlines...")
    distance = build_distance_field(grid)

    print("[3/5] Building elevation map...")
    heightmap = np.zeros((size, size), dtype=np.float64)
    scale = size / (2 * world_radius)

    # Pre-compute territory properties
    elevations = np.array([t["elevation"] for t in territories])
    release_counts = np.array([t.get("release_count", 0) for t in territories], dtype=np.float64)
    max_rc = max(release_counts.max(), 1)
    roughness = np.log1p(release_counts) / np.log1p(max_rc)  # 0-1

    # Scene-based continent merging: territories in same scene get smoothed together
    scene_map = defaultdict(list)
    for idx, t in enumerate(territories):
        scene_map[t["scene"]].append(idx)

    print("[4/5] Generating noise layers...")
    seed_base = 42

    # Pre-generate noise layers using vectorized row processing
    # Build world coordinate grids
    px_coords = np.arange(size)
    wx_all = px_coords / scale - world_radius

    # Elevation and roughness maps (from grid -> territory lookup)
    elev_map = np.where(grid >= 0, elevations[np.clip(grid, 0, len(elevations) - 1)], 0.0)
    rough_map = np.where(grid >= 0, roughness[np.clip(grid, 0, len(roughness) - 1)], 0.0)

    # Generate noise row-by-row (snoise2 is per-point, but we minimize Python overhead)
    base_noise = np.zeros((size, size), dtype=np.float64)
    detail_noise = np.zeros((size, size), dtype=np.float64)
    fine_noise = np.zeros((size, size), dtype=np.float64)

    for py in range(size):
        if py % 256 == 0:
            print(f"       Row {py}/{size}...")
        wy = py / scale - world_radius
        for px in range(size):
            wx = wx_all[px]
            base_noise[py, px] = snoise2(
                wx * NOISE_SCALE + seed_base, wy * NOISE_SCALE + seed_base,
                octaves=4, persistence=0.5, lacunarity=2.0)
            if grid[py, px] >= 0:
                detail_noise[py, px] = snoise2(
                    wx * DETAIL_NOISE_SCALE + seed_base + 100,
                    wy * DETAIL_NOISE_SCALE + seed_base + 100,
                    octaves=NOISE_OCTAVES, persistence=NOISE_PERSISTENCE,
                    lacunarity=NOISE_LACUNARITY)
                fine_noise[py, px] = snoise2(
                    wx * ROUGHNESS_SCALE + seed_base + 200,
                    wy * ROUGHNESS_SCALE + seed_base + 200,
                    octaves=3)

    print("       Compositing terrain...")
    land_mask = grid >= 0

    # Land: elevation + noise detail
    terrain = elev_map + detail_noise * 0.15 + fine_noise * rough_map * 0.08
    coast_factor = np.minimum(1.0, distance / COAST_BLEND)
    terrain = OCEAN_LEVEL + (terrain - OCEAN_LEVEL) * coast_factor
    terrain = np.clip(terrain, OCEAN_LEVEL + 0.01, 1.0)

    # Ocean: shallow near coast, deeper far away
    ocean = OCEAN_LEVEL * 0.5 + base_noise * 0.05
    near_coast = distance > 0.01
    ocean = np.where(near_coast, OCEAN_LEVEL * (0.3 + distance * 2), ocean)
    ocean = np.clip(ocean, 0.0, OCEAN_LEVEL - 0.01)

    heightmap = np.where(land_mask, terrain, ocean)

    print("[5/5] Writing output files...")

    # Normalize to 0-65535 for 16-bit PNG
    hmap_16 = (np.clip(heightmap, 0, 1) * 65535).astype(np.uint16)

    # Write PNG using raw bytes (avoid PIL dependency)
    _write_png_16bit(output_png, hmap_16)
    png_size = os.path.getsize(output_png) / 1024
    print(f"       Heightmap: {output_png} ({png_size:.0f} KB)")

    # Metadata
    meta = {
        "size": size,
        "world_radius": world_radius,
        "ocean_level": OCEAN_LEVEL,
        "elevation_range": [float(heightmap.min()), float(heightmap.max())],
        "land_coverage_pct": round(land_pixels / total_pixels * 100, 1),
        "territory_count": len(territories),
        "continent_count": len(data.get("continents", {})),
        "scene_stats": {
            scene: {
                "territory_count": len(indices),
                "avg_elevation": round(float(elevations[indices].mean()), 3),
            }
            for scene, indices in scene_map.items()
        },
    }

    with open(output_meta, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"       Metadata: {output_meta}")


def _write_png_16bit(path: str, data: np.ndarray):
    """Write a 16-bit grayscale PNG without PIL, using zlib + manual PNG chunks."""
    import struct
    import zlib

    height, width = data.shape

    def make_chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
        c = chunk_type + chunk_data
        crc = zlib.crc32(c) & 0xFFFFFFFF
        return struct.pack(">I", len(chunk_data)) + c + struct.pack(">I", crc)

    # IHDR
    ihdr = struct.pack(">IIBBBBB", width, height, 16, 0, 0, 0, 0)  # 16-bit grayscale

    # IDAT: filter type 0 (None) for each row, big-endian 16-bit values
    raw_rows = bytearray()
    for y in range(height):
        raw_rows.append(0)  # filter byte
        for x in range(width):
            val = int(data[y, x])
            raw_rows.extend(struct.pack(">H", val))

    compressed = zlib.compress(bytes(raw_rows), 9)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(make_chunk(b"IHDR", ihdr))
        f.write(make_chunk(b"IDAT", compressed))
        f.write(make_chunk(b"IEND", b""))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate heightmap from genre territories")
    parser.add_argument("input", nargs="?", default=None, help="Input genre_planet.json path")
    parser.add_argument("--size", type=int, default=HEIGHTMAP_SIZE, help="Heightmap resolution (default: 2048)")
    args = parser.parse_args()

    base = os.path.dirname(os.path.abspath(__file__))
    input_path = args.input or os.path.join(base, "..", "web", "public", "data", "genre_planet.json")
    output_png = os.path.join(base, "..", "web", "public", "data", "genre_heightmap.png")
    output_meta = os.path.join(base, "..", "web", "public", "data", "genre_heightmap_meta.json")

    data = load_territories(input_path)
    generate_heightmap(data, output_png, output_meta, size=args.size)


if __name__ == "__main__":
    main()
