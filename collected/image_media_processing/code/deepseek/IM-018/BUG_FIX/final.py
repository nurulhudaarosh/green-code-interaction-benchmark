import os
import numpy as np
from PIL import Image
from pathlib import Path
from collections import defaultdict

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff', '.webp'}


class UnionFind:
    """Disjoint-set with correct path compression and union by rank."""

    __slots__ = ("parent", "rank")

    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        # Iterative path compression — collect the path first, then compress.
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        # Second pass: point every node on the path directly at root.
        while self.parent[x] != root:
            nxt = self.parent[x]
            self.parent[x] = root
            x = nxt
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


def compute_histogram(path, bins=256):
    try:
        with Image.open(path) as img:
            gray = img.convert('L')
            arr = np.asarray(gray, dtype=np.uint8)
    except Exception as e:
        print(f"  [skip] {path}: {e}")
        return None

    hist, _ = np.histogram(arr, bins=bins, range=(0, 256))
    total = hist.sum()
    if total == 0:
        return None
    return (hist / total).astype(np.float32)


def _cluster_transitively(H, threshold):
    """
    Given an (n, bins) matrix of normalized histograms, return a list of
    clusters (lists of indices) using transitive union-find grouping.

    Two indices i, j are directly linked iff L1(H[i], H[j]) <= threshold.
    The returned clusters are the connected components of that graph.
    """
    n = H.shape[0]
    uf = UnionFind(n)

    # Process in row blocks so memory stays O(block * n) instead of O(n^2).
    # Every close pair (i, j) with j > i triggers a union; union-find then
    # resolves transitivity automatically (A~B, B~C => A,B,C share a root).
    block = 512
    for start in range(0, n, block):
        end = min(start + block, n)
        # (block, 1, bins) - (1, n, bins) -> (block, n, bins)
        d = np.abs(H[start:end, None, :] - H[None, :, :]).sum(axis=2)
        for r in range(end - start):
            i = start + r
            # Only consider j > i so we don't double-count.
            close = np.where(d[r, i + 1:] <= threshold)[0]
            for off in close:
                uf.union(i, i + 1 + int(off))

    groups = defaultdict(list)
    for i in range(n):
        groups[uf.find(i)].append(i)
    return list(groups.values())


def find_near_duplicates(input_dir, threshold, bins=256):
    """
    Cluster images in `input_dir` by normalized grayscale histogram L1
    distance, with transitive (connected-component) grouping via union-find.

    Returns
    -------
    clusters : list[list[str]]
        Each inner list holds absolute paths of one cluster, sorted by path.
        Only clusters with >= 2 members are returned, sorted by descending
        size (ties broken by first path).
    histograms : dict[str, np.ndarray]
        path -> normalized histogram, for inspection.
    """
    input_dir = Path(input_dir).resolve()
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    # --- 1. Discover images ---
    paths = []
    for root, _, files in os.walk(input_dir):
        for fname in files:
            if Path(fname).suffix.lower() in IMAGE_EXTS:
                paths.append(str(Path(root) / fname))
    paths.sort()

    if len(paths) < 2:
        return [], {}

    # --- 2. Histograms ---
    print(f"Found {len(paths)} candidate images. Computing histograms...")
    histograms = {}
    for p in paths:
        h = compute_histogram(p, bins=bins)
        if h is not None:
            histograms[p] = h

    keys = list(histograms.keys())
    n = len(keys)
    if n < 2:
        return [], histograms

    # --- 3. Transitive clustering ---
    H = np.stack([histograms[k] for k in keys])  # (n, bins)
    index_clusters = _cluster_transitively(H, threshold)

    # --- 4. Map back to paths ---
    clusters = [
        sorted(keys[i] for i in members)
        for members in index_clusters
        if len(members) >= 2
    ]
    clusters.sort(key=lambda c: (-len(c), c[0]))

    return clusters, histograms


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python find_near_duplicates.py <input_dir> <threshold> [bins]")
        sys.exit(1)

    directory = sys.argv[1]
    thr = float(sys.argv[2])
    nbins = int(sys.argv[3]) if len(sys.argv) > 3 else 256

    clusters, _ = find_near_duplicates(directory, thr, bins=nbins)

    print(f"\nFound {len(clusters)} transitive cluster(s) "
          f"(threshold={thr}, bins={nbins}):\n")
    for idx, cluster in enumerate(clusters, 1):
        print(f"Cluster #{idx}  ({len(cluster)} images)")
        for p in cluster:
            print(f"    {p}")
        print()