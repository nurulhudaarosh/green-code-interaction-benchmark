"""Cluster near-duplicate images by grayscale histogram L1 distance."""

from pathlib import Path

import numpy as np
from PIL import Image

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
    """256-bin grayscale histogram divided by pixel count (sums to 1)."""
    with Image.open(path) as img:
        hist = np.asarray(img.convert("L").histogram(), dtype=np.float64)
    total = hist.sum()
    if total == 0:
        raise ValueError("empty image")
    return hist / total


def find_near_duplicates(input_dir, threshold, recursive=False):
    """Group images in `input_dir` whose normalized grayscale histograms are close.

    Two images are linked if the L1 distance between their normalized
    histograms is <= `threshold` (range is 0 for identical to 2 for disjoint).
    Links are transitive: if A~B and B~C, then A, B, C share a cluster
    even if A and C are individually farther apart than `threshold`.

    Returns a list of clusters (lists of path strings, sorted), containing
    only clusters with at least two images. Clusters are ordered by their
    first member. Unreadable files are skipped.
    """
    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    root = Path(input_dir)
    if not root.is_dir():
        raise NotADirectoryError(f"{input_dir} is not a directory")

    candidates = root.rglob("*") if recursive else root.iterdir()
    files = sorted(
        p for p in candidates if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    paths, hists = [], []
    for p in files:
        try:
            hists.append(_normalized_histogram(p))
            paths.append(str(p))
        except Exception:
            continue  # corrupt / unsupported image

    n = len(paths)
    if n < 2:
        return []

    H = np.vstack(hists)
    uf = UnionFind(n)

    for i in range(n - 1):
        dists = np.abs(H[i + 1:] - H[i]).sum(axis=1)
        for offset in np.nonzero(dists <= threshold)[0]:
            uf.union(i, i + 1 + int(offset))

    groups = {}
    for i in range(n):
        groups.setdefault(uf.find(i), []).append(paths[i])

    clusters = [sorted(g) for g in groups.values() if len(g) > 1]
    clusters.sort(key=lambda g: g[0])
    return clusters


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        sys.exit("usage: python near_duplicates.py <input_dir> <threshold>")
    for cluster in find_near_duplicates(sys.argv[1], float(sys.argv[2])):
        print(cluster)