"""Cluster near-duplicate images by grayscale-histogram L1 distance."""

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
    """256-bin grayscale histogram normalized to sum to 1 (None if unreadable)."""
    try:
        with Image.open(path) as img:
            hist = np.asarray(img.convert("L").histogram(), dtype=np.float64)
    except (UnidentifiedImageError, OSError):
        return None
    total = hist.sum()
    return hist / total if total > 0 else None


def find_near_duplicates(input_dir, threshold):
    """Group images in `input_dir` whose histograms are within `threshold`.

    Distance is the L1 distance between normalized grayscale histograms,
    which ranges from 0 (identical) to 2 (disjoint). Two images are linked
    if distance <= threshold; groups are the connected components of that
    graph (transitive, via union-find), so A~B and B~C puts A, B, C together
    even if A and C are farther apart than `threshold`.

    Returns a list of clusters (lists of path strings, sorted), each with
    at least two images, ordered by descending size then first path.
    Unreadable or non-image files are skipped.
    """
    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    root = Path(input_dir)
    if not root.is_dir():
        raise NotADirectoryError(f"{input_dir!r} is not a directory")

    paths, hists = [], []
    for p in sorted(root.iterdir()):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
            h = _normalized_histogram(p)
            if h is not None:
                paths.append(str(p))
                hists.append(h)

    n = len(paths)
    if n < 2:
        return []

    matrix = np.stack(hists)  # (n, 256)
    uf = UnionFind(n)

    # Row-by-row keeps memory at O(n * 256) instead of O(n^2 * 256).
    for i in range(n - 1):
        dists = np.abs(matrix[i + 1:] - matrix[i]).sum(axis=1)
        for offset in np.nonzero(dists <= threshold)[0]:
            uf.union(i, i + 1 + int(offset))

    groups = {}
    for i in range(n):
        groups.setdefault(uf.find(i), []).append(paths[i])

    clusters = [sorted(g) for g in groups.values() if len(g) > 1]
    clusters.sort(key=lambda g: (-len(g), g[0]))
    return clusters


if __name__ == "__main__":
    import sys

    directory = sys.argv[1]
    thresh = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05
    for k, cluster in enumerate(find_near_duplicates(directory, thresh), 1):
        print(f"Cluster {k}:")
        for path in cluster:
            print(f"  {path}")