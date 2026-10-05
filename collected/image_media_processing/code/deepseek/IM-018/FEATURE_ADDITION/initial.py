import os
from collections import defaultdict
from PIL import Image
import numpy as np


def _compute_normalized_histogram(path, bins=64):
    """Load an image, convert to grayscale, return an L1-normalized histogram."""
    with Image.open(path) as img:
        gray = img.convert("L")
        arr = np.asarray(gray, dtype=np.uint8)
    hist, _ = np.histogram(arr, bins=bins, range=(0, 256))
    hist = hist.astype(np.float64)
    total = hist.sum()
    if total > 0:
        hist /= total
    return hist


class _UnionFind:
    """Disjoint-set with path compression and union by rank."""

    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        # Path compression
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def find_near_duplicates(input_dir, threshold):
    """
    Cluster images in `input_dir` by L1 distance between normalized
    grayscale histograms. Two images are neighbors if
    sum(|h_i - h_j|) <= threshold. Groups are formed by transitive
    closure (union-find), so A~B and B~C puts A, B, C in one cluster.

    Args:
        input_dir: Directory containing images (searched non-recursively).
        threshold: Maximum L1 distance in [0, 2] to consider near-duplicates.

    Returns:
        List of clusters; each cluster is a sorted list of file paths.
        Singleton clusters (no duplicates found) are excluded.
    """
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}

    paths, hists = [], []
    for name in sorted(os.listdir(input_dir)):
        full = os.path.join(input_dir, name)
        if not os.path.isfile(full):
            continue
        if os.path.splitext(name)[1].lower() not in valid_exts:
            continue
        try:
            hists.append(_compute_normalized_histogram(full))
            paths.append(full)
        except (OSError, ValueError) as exc:
            print(f"Skipping {full}: {exc}")

    n = len(paths)
    if n < 2:
        return []

    # Stack histograms into a matrix for vectorized pairwise comparison.
    H = np.vstack(hists)                 # shape (n, bins)
    uf = _UnionFind(n)

    # Row-wise L1 distance: |H[i] - H[j]| summed over bins.
    # We only need pairs (i, j) with i < j.
    for i in range(n - 1):
        # Broadcasting row i against all later rows.
        diff = np.abs(H[i + 1:] - H[i]).sum(axis=1)
        for j_offset in np.nonzero(diff <= threshold)[0]:
            uf.union(i, i + 1 + int(j_offset))

    # Group paths by root.
    groups = defaultdict(list)
    for idx, path in enumerate(paths):
        groups[uf.find(idx)].append(path)

    clusters = [sorted(members) for members in groups.values() if len(members) > 1]
    clusters.sort(key=lambda c: c[0])
    return clusters


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python find_near_duplicates.py <input_dir> <threshold>")
        sys.exit(1)
    directory = sys.argv[1]
    thresh = float(sys.argv[2])
    for cluster in find_near_duplicates(directory, thresh):
        print("Cluster:")
        for p in cluster:
            print("  ", p)