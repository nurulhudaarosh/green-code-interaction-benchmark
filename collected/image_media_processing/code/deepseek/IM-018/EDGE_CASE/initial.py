import os
from pathlib import Path
from itertools import combinations

import numpy as np
from PIL import Image

# Optional: for faster image loading of many formats
try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}
HIST_BINS = 256


class UnionFind:
    """Disjoint-set / union-find with path compression and union by rank."""

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

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True


def _load_histogram(path, bins=HIST_BINS):
    """Load image, convert to grayscale, return normalized L1 histogram (sums to 1)."""
    try:
        if _HAS_CV2:
            # cv2.imread handles unicode paths poorly on some platforms; use fromfile
            data = np.fromfile(str(path), dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return None
        else:
            with Image.open(path) as im:
                img = np.asarray(im.convert("L"))
    except Exception:
        return None

    hist, _ = np.histogram(img, bins=bins, range=(0, 256))
    total = hist.sum()
    if total == 0:
        return None
    return hist.astype(np.float64) / total


def find_near_duplicates(input_dir, threshold):
    """
    Cluster images in `input_dir` whose normalized grayscale histograms have
    L1 distance <= `threshold`.

    Transitive grouping: if A~B and B~C, then A, B, C are in the same cluster
    even if A and C exceed the threshold (union-find).

    Parameters
    ----------
    input_dir : str | os.PathLike
        Directory to scan (recursively) for images.
    threshold : float
        Maximum L1 distance between normalized histograms (range 0.0 - 2.0).

    Returns
    -------
    list[list[str]]
        A list of clusters. Each cluster is a list of file paths. Only clusters
        with 2+ members are returned (singletons are dropped). Sorted by
        descending cluster size, then by first path.
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    # 1. Collect image paths
    paths = sorted(
        p for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )

    # 2. Compute histograms
    hists = []
    valid_paths = []
    for p in paths:
        h = _load_histogram(p)
        if h is not None:
            hists.append(h)
            valid_paths.append(p)

    n = len(valid_paths)
    if n < 2:
        return []

    hists = np.vstack(hists)  # (n, bins)

    # 3. Union-find over all pairs; O(n^2) comparisons.
    #    For very large sets, use a cheaper prefilter (e.g. lsh / bucketing).
    uf = UnionFind(n)
    for i, j in combinations(range(n), 2):
        # L1 distance between normalized histograms
        d = np.abs(hists[i] - hists[j]).sum()
        if d <= threshold:
            uf.union(i, j)

    # 4. Group members by root
    clusters = {}
    for i in range(n):
        root = uf.find(i)
        clusters.setdefault(root, []).append(str(valid_paths[i]))

    # 5. Keep only clusters with 2+ members, sort
    result = [sorted(members) for members in clusters.values() if len(members) > 1]
    result.sort(key=lambda c: (-len(c), c[0]))
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python find_near_duplicates.py <input_dir> <threshold>")
        sys.exit(1)

    folder = sys.argv[1]
    thr = float(sys.argv[2])

    clusters = find_near_duplicates(folder, thr)
    if not clusters:
        print("No near-duplicate clusters found.")
    else:
        for idx, cluster in enumerate(clusters, 1):
            print(f"Cluster {idx} ({len(cluster)} images):")
            for path in cluster:
                print(f"  {path}")