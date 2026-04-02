"""
Content-based similarity index for vinyl releases.
Feature vector: style_ids (binary) + label overlap (0.5 weight).
Uses sparse matrix + cosine similarity from scikit-learn.
"""
import json
import sqlite3
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


def build_feature_vectors(releases: list[dict], all_styles: list[str] | None = None):
    """Build sparse feature vectors from release metadata.

    Each release gets a row with binary style features (weight 1.0)
    and a label feature (weight 0.5).
    """
    if all_styles is None:
        all_styles = sorted(set(s for r in releases for s in r.get("styles", [])))
    style_idx = {s: i for i, s in enumerate(all_styles)}

    all_labels = sorted(set(r.get("label", "") for r in releases if r.get("label")))
    label_idx = {label: i + len(all_styles) for i, label in enumerate(all_labels)}

    n_features = len(all_styles) + len(all_labels)
    rows, cols, data = [], [], []
    id_to_row = {}

    for row_i, release in enumerate(releases):
        rid = release.get("id", row_i)
        id_to_row[rid] = row_i

        for style in release.get("styles", []):
            if style in style_idx:
                rows.append(row_i)
                cols.append(style_idx[style])
                data.append(1.0)

        label = release.get("label", "")
        if label and label in label_idx:
            rows.append(row_i)
            cols.append(label_idx[label])
            data.append(0.5)

    matrix = csr_matrix((data, (rows, cols)), shape=(len(releases), n_features))
    return {
        "matrix": matrix,
        "id_to_row": id_to_row,
        "row_to_id": {v: k for k, v in id_to_row.items()},
    }


def find_neighbors(
    vectors: dict, release_id: int, top_n: int = 10
) -> list[tuple[int, float]]:
    """Find top_n most similar releases by cosine similarity."""
    row = vectors["id_to_row"].get(release_id)
    if row is None:
        return []

    query = vectors["matrix"][row]
    similarities = cosine_similarity(query, vectors["matrix"]).flatten()
    similarities[row] = -1  # exclude self

    top_indices = np.argsort(similarities)[-top_n:][::-1]
    return [
        (vectors["row_to_id"][i], float(similarities[i]))
        for i in top_indices
        if similarities[i] > 0
    ]


def build_and_store_neighbors(
    conn: sqlite3.Connection, top_n: int = 50, vinyl_only: bool = True
):
    """Build similarity index from DB releases and store neighbor pairs."""
    query = "SELECT id, styles, label, year FROM releases"
    if vinyl_only:
        query += " WHERE format = 'Vinyl'"

    cursor = conn.execute(query)
    releases = []
    for row in cursor:
        releases.append({
            "id": row[0],
            "styles": json.loads(row[1]) if row[1] else [],
            "label": row[2] or "",
            "year": row[3] or 0,
        })

    if not releases:
        print("No releases found for similarity index")
        return

    print(f"Building similarity index for {len(releases):,} releases...")
    vectors = build_feature_vectors(releases)

    batch = []
    for i, release in enumerate(releases):
        neighbors = find_neighbors(vectors, release["id"], top_n=top_n)
        for neighbor_id, score in neighbors:
            batch.append((release["id"], neighbor_id, round(score, 4)))

        if len(batch) >= 10000:
            conn.executemany(
                "INSERT OR REPLACE INTO release_neighbors VALUES (?, ?, ?)", batch
            )
            conn.commit()
            batch = []

        if (i + 1) % 1000 == 0:
            print(f"  ... {i + 1:,}/{len(releases):,} releases indexed")

    if batch:
        conn.executemany(
            "INSERT OR REPLACE INTO release_neighbors VALUES (?, ?, ?)", batch
        )
        conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM release_neighbors").fetchone()[0]
    print(f"Similarity index complete: {total:,} neighbor pairs")
