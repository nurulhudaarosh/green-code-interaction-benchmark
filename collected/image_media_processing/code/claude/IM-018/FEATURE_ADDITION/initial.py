"""Cluster near-duplicate images by grayscale histogram L1 distance."""

from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


class UnionFind:
    """Disjoint-set with path compression and union by size."""

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # path compression
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]


def _normalized_histogram(path):
    """256-bin grayscale histogram, scaled to sum to 1 (size-independent)."""
    with Image.open(path) as img:
        hist = np.asarray(img.convert("L").histogram(), dtype=np.float64)
    total = hist.sum()
    return hist / total if total > 0 else None


def find_near_duplicates(input_dir, threshold):
    """
    Group images in `input_dir` (recursively) whose normalized grayscale
    histograms are within `threshold` L1 distance of each other.

    L1 distance between two normalized histograms lies in [0, 2]; 0 means
    identical distributions. Grouping is transitive: if A~B and B~C, then
    A, B, C land in the same cluster even if A and C differ by more than
    `threshold`.

    Returns a list of clusters (each a sorted list of path strings) with at
    least two members, ordered largest first. Unreadable files are skipped.
    """
    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    paths, hists = [], []
    for p in sorted(Path(input_dir).rglob("*")):
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        try:
            h = _normalized_histogram(p)
        except (UnidentifiedImageError, OSError, ValueError):
            continue
        if h is not None:
            paths.append(str(p))
            hists.append(h)

    n = len(paths)
    if n < 2:
        return []

    matrix = np.stack(hists)  # (n, 256)
    uf = UnionFind(n)

    # Compare each image against all later ones in one vectorized step.
    for i in range(n - 1):
        dists = np.abs(matrix[i + 1:] - matrix[i]).sum(axis=1)
        for j in np.nonzero(dists <= threshold)[0]:
            uf.union(i, i + 1 + int(j))

    groups = {}
    for idx in range(n):
        groups.setdefault(uf.find(idx), []).append(paths[idx])

    clusters = [sorted(g) for g in groups.values() if len(g) > 1]
    clusters.sort(key=lambda g: (-len(g), g[0]))
    return clusters


if __name__ == "__main__":
    import sys

    directory = sys.argv[1]
    thresh = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05
    for k, cluster in enumerate(find_near_duplicates(directory, thresh), 1):
        print(f"Cluster {k} ({len(cluster)} images):")
        for path in cluster:
            print(f"  {path}")