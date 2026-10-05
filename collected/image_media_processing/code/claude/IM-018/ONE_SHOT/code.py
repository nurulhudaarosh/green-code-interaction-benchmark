"""Cluster near-duplicate images by grayscale histogram L1 distance."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


class UnionFind:
    """Disjoint-set with path compression and union by size."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n

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
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]


def _normalized_histogram(path: Path, bins: int = 256) -> np.ndarray:
    """Grayscale histogram divided by pixel count (sums to 1)."""
    with Image.open(path) as img:
        gray = np.asarray(img.convert("L"))
    hist, _ = np.histogram(gray, bins=bins, range=(0, 256))
    total = hist.sum()
    if total == 0:
        raise ValueError("empty image")
    return hist.astype(np.float64) / total


def find_near_duplicates(input_dir, threshold: float = 0.1, recursive: bool = True):
    """Group images in ``input_dir`` whose histograms are close.

    Each image is converted to grayscale and reduced to a 256-bin histogram
    normalized to sum to 1, so image size doesn't matter. Two images are
    "similar" if the L1 distance between histograms is <= ``threshold``
    (the distance lies in [0, 2]; 0 means identical histograms).

    Grouping is transitive: if A~B and B~C, then A, B, C share a cluster
    even when A and C are farther apart than ``threshold``. This is done
    with union-find.

    Returns a list of clusters (each a sorted list of path strings) with at
    least two members, sorted by descending size then first path. Files that
    can't be read as images are skipped.
    """
    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    root = Path(input_dir)
    if not root.is_dir():
        raise NotADirectoryError(f"{input_dir} is not a directory")

    files = root.rglob("*") if recursive else root.glob("*")
    candidates = sorted(
        p for p in files if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    paths: list[Path] = []
    hists: list[np.ndarray] = []
    for p in candidates:
        try:
            hists.append(_normalized_histogram(p))
            paths.append(p)
        except (OSError, UnidentifiedImageError, ValueError):
            continue

    n = len(paths)
    if n < 2:
        return []

    matrix = np.vstack(hists)  # (n, 256)
    uf = UnionFind(n)

    # Vectorized pairwise L1 distance, one row at a time: O(n^2 * bins) time, O(n * bins) memory.
    for i in range(n - 1):
        dists = np.abs(matrix[i + 1:] - matrix[i]).sum(axis=1)
        for j in np.nonzero(dists <= threshold)[0]:
            uf.union(i, i + 1 + int(j))

    groups: dict[int, list[str]] = {}
    for i, p in enumerate(paths):
        groups.setdefault(uf.find(i), []).append(str(p))

    clusters = [sorted(g) for g in groups.values() if len(g) > 1]
    clusters.sort(key=lambda g: (-len(g), g[0]))
    return clusters


if __name__ == "__main__":
    import sys

    directory = sys.argv[1]
    thr = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
    for k, cluster in enumerate(find_near_duplicates(directory, thr), 1):
        print(f"Cluster {k} ({len(cluster)} images):")
        for path in cluster:
            print(f"  {path}")