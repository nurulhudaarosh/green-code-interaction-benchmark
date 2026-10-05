"""Cluster near-duplicate images by grayscale histogram L1 distance."""

from __future__ import annotations

import os
from typing import Dict, List

import numpy as np
from PIL import Image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


class UnionFind:
    """Disjoint-set with path compression and union by rank."""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # path compression
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def _normalized_histogram(path: str) -> np.ndarray:
    """256-bin grayscale histogram, normalized to sum to 1."""
    with Image.open(path) as img:
        gray = img.convert("L")
        hist = np.asarray(gray.histogram(), dtype=np.float64)
    total = hist.sum()
    return hist / total if total > 0 else hist


def find_near_duplicates(
    input_dir: str, threshold: float, recursive: bool = False
) -> List[List[str]]:
    """Group images in `input_dir` whose normalized grayscale histograms are close.

    Two images are linked if the L1 distance between their normalized
    256-bin grayscale histograms is <= `threshold`. The L1 distance lies in
    [0, 2] (0 = identical distribution, 2 = disjoint). Links are transitive:
    if A~B and B~C, then A, B and C land in the same cluster even if A and C
    are farther apart than `threshold`. Grouping uses union-find.

    Args:
        input_dir: Directory containing images.
        threshold: Maximum L1 distance (inclusive) for two images to be linked.
        recursive: Also scan subdirectories.

    Returns:
        A list of clusters, each a sorted list of file paths. Only clusters
        with at least two images are returned. Clusters are ordered by their
        first path. Unreadable/non-image files are skipped.
    """
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(input_dir)

    # Collect candidate files in deterministic order.
    candidates: List[str] = []
    if recursive:
        for root, _, files in os.walk(input_dir):
            candidates.extend(os.path.join(root, f) for f in files)
    else:
        candidates = [
            os.path.join(input_dir, f)
            for f in os.listdir(input_dir)
            if os.path.isfile(os.path.join(input_dir, f))
        ]
    candidates = sorted(
        p for p in candidates if os.path.splitext(p)[1].lower() in IMAGE_EXTENSIONS
    )

    paths: List[str] = []
    hists: List[np.ndarray] = []
    for p in candidates:
        try:
            hists.append(_normalized_histogram(p))
            paths.append(p)
        except Exception:
            continue  # unreadable or corrupt image

    n = len(paths)
    if n < 2:
        return []

    H = np.vstack(hists)  # shape (n, 256)
    uf = UnionFind(n)

    # Pairwise L1 distances, vectorized one row at a time (O(n^2 * 256) time, O(n) extra memory).
    for i in range(n - 1):
        dists = np.abs(H[i + 1:] - H[i]).sum(axis=1)
        for offset in np.nonzero(dists <= threshold)[0]:
            uf.union(i, i + 1 + int(offset))

    groups: Dict[int, List[str]] = {}
    for idx, p in enumerate(paths):
        groups.setdefault(uf.find(idx), []).append(p)

    clusters = [sorted(g) for g in groups.values() if len(g) > 1]
    clusters.sort(key=lambda g: g[0])
    return clusters


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        sys.exit("usage: python near_duplicates.py <input_dir> <threshold>")
    for i, cluster in enumerate(find_near_duplicates(sys.argv[1], float(sys.argv[2])), 1):
        print(f"Cluster {i}:")
        for path in cluster:
            print(f"  {path}")