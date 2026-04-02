"""
Build item-based collaborative filtering model from crawled public collections.

Uses the Implicit library (ALS matrix factorization) to find "crate neighbors" —
releases commonly found in the same vinyl collections.

Usage:
    python3 collaborative_filter.py
    python3 collaborative_filter.py --top-n 50 --factors 64

Input:  discoworld_cf.db (public_collections table from collection_crawler.py)
Output: cf_neighbors table in discoworld_cf.db (release_id, neighbor_id, score)
"""

import argparse
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix

try:
    from implicit.als import AlternatingLeastSquares
except ImportError:
    print("ERROR: implicit library not installed. Run: pip install implicit")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CF_DB_PATH = DATA_DIR / "discoworld_cf.db"

CF_NEIGHBORS_SCHEMA = """
CREATE TABLE IF NOT EXISTS cf_neighbors (
    release_id INTEGER NOT NULL,
    neighbor_id INTEGER NOT NULL,
    score REAL NOT NULL,
    PRIMARY KEY (release_id, neighbor_id)
);

CREATE INDEX IF NOT EXISTS idx_cfn_release ON cf_neighbors(release_id);
CREATE INDEX IF NOT EXISTS idx_cfn_score ON cf_neighbors(score DESC);
"""


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_interaction_matrix(conn: sqlite3.Connection) -> tuple[csr_matrix, dict, dict]:
    """Load user-item interactions from public_collections.

    Returns:
        matrix: sparse user x item matrix (binary: 1 = user owns item)
        user_map: {user_hash -> row_index}
        item_map: {release_id -> col_index}
    """
    print("Loading interaction data...")

    # Get all unique users and items
    users = conn.execute(
        "SELECT DISTINCT user_hash FROM public_collections"
    ).fetchall()
    items = conn.execute(
        "SELECT DISTINCT release_id FROM public_collections"
    ).fetchall()

    user_map = {r[0]: i for i, r in enumerate(users)}
    item_map = {r[0]: i for i, r in enumerate(items)}

    print(f"  Users: {len(user_map):,}")
    print(f"  Items: {len(item_map):,}")

    # Build sparse matrix
    rows = []
    cols = []
    data = []

    # Stream in batches for memory efficiency
    cursor = conn.execute("SELECT user_hash, release_id FROM public_collections")
    batch_size = 100_000
    total = 0

    while True:
        batch = cursor.fetchmany(batch_size)
        if not batch:
            break
        for user_hash, release_id in batch:
            row = user_map.get(user_hash)
            col = item_map.get(release_id)
            if row is not None and col is not None:
                rows.append(row)
                cols.append(col)
                data.append(1.0)
                total += 1

    print(f"  Interactions: {total:,}")

    matrix = coo_matrix(
        (data, (rows, cols)),
        shape=(len(user_map), len(item_map)),
    ).tocsr()

    return matrix, user_map, item_map


def filter_sparse_items(
    matrix: csr_matrix,
    item_map: dict[int, int],
    min_users: int = 2,
) -> tuple[csr_matrix, dict]:
    """Remove items with fewer than min_users interactions.

    Returns filtered matrix and updated item_map.
    """
    item_counts = np.diff(matrix.tocsc().indptr)
    keep_cols = np.where(item_counts >= min_users)[0]

    if len(keep_cols) == len(item_counts):
        return matrix, item_map

    # Rebuild item_map for kept columns only
    inv_map = {v: k for k, v in item_map.items()}
    new_item_map = {}
    col_mapping = {}
    for new_idx, old_idx in enumerate(keep_cols):
        release_id = inv_map[old_idx]
        new_item_map[release_id] = new_idx
        col_mapping[old_idx] = new_idx

    # Rebuild matrix with only kept columns
    coo = matrix.tocoo()
    mask = np.isin(coo.col, keep_cols)
    new_cols = np.array([col_mapping[c] for c in coo.col[mask]])
    filtered = coo_matrix(
        (coo.data[mask], (coo.row[mask], new_cols)),
        shape=(matrix.shape[0], len(keep_cols)),
    ).tocsr()

    removed = len(item_counts) - len(keep_cols)
    print(f"  Filtered {removed:,} items with < {min_users} users -> {len(keep_cols):,} items remaining")

    return filtered, new_item_map


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------


def train_als_model(
    matrix: csr_matrix,
    factors: int = 64,
    regularization: float = 0.01,
    iterations: int = 15,
) -> AlternatingLeastSquares:
    """Train ALS model on user-item interaction matrix.

    The Implicit library expects item-user matrix (items x users),
    so we transpose our user-item matrix.
    """
    print(f"Training ALS model (factors={factors}, iterations={iterations})...")
    t0 = time.time()

    model = AlternatingLeastSquares(
        factors=factors,
        regularization=regularization,
        iterations=iterations,
        use_gpu=False,
    )

    # Implicit expects item-user matrix
    item_user_matrix = matrix.T.tocsr()
    model.fit(item_user_matrix)

    elapsed = time.time() - t0
    print(f"  Training complete in {elapsed:.1f}s")

    return model


# ---------------------------------------------------------------------------
# Neighbor extraction
# ---------------------------------------------------------------------------


def extract_neighbors(
    model: AlternatingLeastSquares,
    item_map: dict[int, int],
    top_n: int = 50,
) -> list[tuple[int, int, float]]:
    """Extract top-N similar items for each item in the model.

    Returns list of (release_id, neighbor_id, score) tuples.
    """
    inv_map = {v: k for k, v in item_map.items()}
    item_ids = sorted(item_map.values())
    total_items = len(item_ids)

    print(f"Extracting top-{top_n} neighbors for {total_items:,} items...")
    t0 = time.time()

    results = []

    # Process in batches for efficiency
    batch_size = 1000
    for start in range(0, total_items, batch_size):
        end = min(start + batch_size, total_items)
        batch_ids = item_ids[start:end]

        # similar_items returns (ids, scores) arrays
        ids_batch, scores_batch = model.similar_items(
            batch_ids, N=top_n + 1  # +1 because item itself is included
        )

        for i, item_idx in enumerate(batch_ids):
            release_id = inv_map.get(item_idx)
            if release_id is None:
                continue

            for j in range(ids_batch.shape[1]):
                neighbor_idx = int(ids_batch[i, j])
                score = float(scores_batch[i, j])

                if neighbor_idx == item_idx:
                    continue  # Skip self
                if score <= 0:
                    continue

                neighbor_release_id = inv_map.get(neighbor_idx)
                if neighbor_release_id is None:
                    continue

                results.append((release_id, neighbor_release_id, round(score, 6)))

        if (start + batch_size) % 10000 == 0 or end == total_items:
            print(f"  ... {end:,}/{total_items:,} items processed")

    elapsed = time.time() - t0
    print(f"  Extracted {len(results):,} neighbor pairs in {elapsed:.1f}s")

    return results


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------


def store_neighbors(conn: sqlite3.Connection, neighbors: list[tuple[int, int, float]]):
    """Store neighbor pairs in the cf_neighbors table."""
    print(f"Storing {len(neighbors):,} neighbor pairs...")

    conn.executescript(CF_NEIGHBORS_SCHEMA)

    # Clear existing data
    conn.execute("DELETE FROM cf_neighbors")

    # Insert in batches
    batch_size = 10_000
    for i in range(0, len(neighbors), batch_size):
        batch = neighbors[i:i + batch_size]
        conn.executemany(
            "INSERT OR REPLACE INTO cf_neighbors (release_id, neighbor_id, score) VALUES (?, ?, ?)",
            batch,
        )
        conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM cf_neighbors").fetchone()[0]
    print(f"  Stored {total:,} neighbor pairs")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_collaborative_filter(
    db_path: Path | None = None,
    factors: int = 64,
    top_n: int = 50,
    min_users: int = 2,
):
    """Full pipeline: load data -> train ALS -> extract neighbors -> store."""
    path = db_path or CF_DB_PATH

    if not path.exists():
        print(f"ERROR: CF database not found at {path}")
        print("Run collection_crawler.py first to gather data.")
        sys.exit(1)

    conn = sqlite3.connect(path)

    # Check we have enough data
    user_count = conn.execute(
        "SELECT COUNT(DISTINCT user_hash) FROM public_collections"
    ).fetchone()[0]
    pair_count = conn.execute(
        "SELECT COUNT(*) FROM public_collections"
    ).fetchone()[0]

    print(f"CF database: {user_count:,} users, {pair_count:,} interaction pairs")

    if user_count < 10:
        print("WARNING: Very few users. Results may not be meaningful.")
        print("Run collection_crawler.py with --target 100+ first.")

    # Load and filter
    matrix, user_map, item_map = load_interaction_matrix(conn)
    matrix, item_map = filter_sparse_items(matrix, item_map, min_users=min_users)

    if matrix.shape[1] < 10:
        print("ERROR: Too few items after filtering. Need more data.")
        conn.close()
        sys.exit(1)

    # Train
    model = train_als_model(matrix, factors=factors)

    # Extract neighbors
    neighbors = extract_neighbors(model, item_map, top_n=top_n)

    # Store
    store_neighbors(conn, neighbors)

    # Summary
    print(f"\n--- Collaborative Filter Complete ---")
    print(f"Model: ALS with {factors} factors")
    print(f"Items with neighbors: {len(item_map):,}")
    print(f"Total neighbor pairs: {len(neighbors):,}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Build collaborative filtering model from crawled collections"
    )
    parser.add_argument(
        "--factors", type=int, default=64,
        help="Number of latent factors for ALS (default: 64)"
    )
    parser.add_argument(
        "--top-n", type=int, default=50,
        help="Number of neighbors per item (default: 50)"
    )
    parser.add_argument(
        "--min-users", type=int, default=2,
        help="Minimum users owning an item to include it (default: 2)"
    )
    parser.add_argument(
        "--db-path", type=str,
        help="Custom database path"
    )
    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else None
    build_collaborative_filter(
        db_path=db_path,
        factors=args.factors,
        top_n=args.top_n,
        min_users=args.min_users,
    )


if __name__ == "__main__":
    main()
