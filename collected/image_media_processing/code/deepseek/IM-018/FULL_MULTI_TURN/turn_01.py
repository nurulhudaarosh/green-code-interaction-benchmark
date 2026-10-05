import os
from pathlib import Path
from collections import defaultdict
import numpy as np
from PIL import Image


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff', '.webp'}


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        # Path compression (iterative)
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        # Union by rank
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True

    def groups(self):
        """Return a dict mapping root -> list of member indices."""
        result = defaultdict(list)
        for i in range(len(self.parent)):
            result[self.find(i)].append(i)
        return result


def compute_histogram(path, bins=256, size=(256, 256)):
    """Load image, convert to grayscale, resize, compute normalized histogram."""
    with Image.open(path) as img:
        img = img.convert('L')
        if size is not None:
            img = img.resize(size, Image.BILINEAR)
        arr = np.asarray(img, dtype=np.uint8)

    hist, _ = np.histogram(arr, bins=bins, range=(0, 256))
    hist = hist.astype(np.float64)

    total = hist.sum()
    if total > 0:
        hist /= total
    return hist


def l1_distance(h1, h2):
    """L1 (Manhattan) distance between two histograms."""
    return float(np.abs(h1 - h2).sum())


def find_near_duplicates(input_dir, threshold, bins=256, size=(256, 256), verbose=False):
    """
    Cluster images in `input_dir` whose normalized grayscale histograms
    are within `threshold` L1 distance, using transitive union-find grouping.

    Parameters
    ----------
    input_dir : str | Path
        Directory to scan (non-recursive).
    threshold : float
        Max L1 distance between two normalized histograms to be considered
        near-duplicates. Range [0, 2] for normalized histograms.
    bins : int
        Number of histogram bins.
    size : tuple | None
        Resize target before histogram computation (None to skip resizing).
    verbose : bool
        Print progress info.

    Returns
    -------
    clusters : list[list[str]]
        List of clusters; each cluster is a list of file paths. Only clusters
        with >= 2 members are returned. Singletons are excluded.
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    # Collect candidate image paths
    paths = sorted(
        str(p) for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if verbose:
        print(f"Found {len(paths)} image(s) in {input_dir}")

    # Compute histograms; skip images that fail to load
    valid_paths = []
    histograms = []
    for p in paths:
        try:
            h = compute_histogram(p, bins=bins, size=size)
            valid_paths.append(p)
            histograms.append(h)
        except Exception as e:
            if verbose:
                print(f"  Skipping {p}: {e}")

    n = len(valid_paths)
    if n < 2:
        return []

    if verbose:
        print(f"Computed histograms for {n} image(s); comparing pairs...")

    # O(n^2) pairwise comparison with union-find.
    # For large datasets, replace with an LSH / bucketing scheme.
    uf = UnionFind(n)
    stacked = np.stack(histograms, axis=0)  # shape (n, bins)

    comparisons = 0
    for i in range(n):
        # Vectorized L1 against all j > i
        diffs = np.abs(stacked[i + 1:] - stacked[i]).sum(axis=1)
        close = np.nonzero(diffs <= threshold)[0]
        for offset in close:
            j = i + 1 + int(offset)
            uf.union(i, j)
            comparisons += 1

    if verbose:
        print(f"Performed {comparisons} union(s) below threshold {threshold}")

    # Build clusters, dropping singletons
    clusters = []
    for members in uf.groups().values():
        if len(members) >= 2:
            clusters.append(sorted(valid_paths[m] for m in members))

    # Sort clusters by size (largest first), then by first path for determinism
    clusters.sort(key=lambda c: (-len(c), c[0]))
    return clusters


# --- Example usage ---------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python find_near_duplicates.py <input_dir> <threshold>")
        sys.exit(1)

    directory = sys.argv[1]
    thr = float(sys.argv[2])

    results = find_near_duplicates(directory, thr, verbose=True)

    if not results:
        print("No near-duplicate clusters found.")
    else:
        print(f"\nFound {len(results)} cluster(s):")
        for idx, cluster in enumerate(results, 1):
            print(f"\nCluster {idx} ({len(cluster)} images):")
            for path in cluster:
                print(f"  {path}")