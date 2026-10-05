import os
import numpy as np
from PIL import Image
from collections import defaultdict

# Optional acceleration for pairwise distance computation
try:
    from scipy.spatial.distance import cdist
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff', '.webp'}


class UnionFind:
    """Disjoint-set forest with path compression and union by rank."""

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

    def groups(self):
        """Return dict {root: [members]}."""
        out = defaultdict(list)
        for i in range(len(self.parent)):
            out[self.find(i)].append(i)
        return out


def _normalized_grayscale_histogram(path, bins=256):
    """Load image, convert to grayscale, return L1-normalized histogram."""
    with Image.open(path) as img:
        gray = img.convert('L')
        arr = np.asarray(gray, dtype=np.uint8)
    hist, _ = np.histogram(arr, bins=bins, range=(0, 256))
    hist = hist.astype(np.float64)
    total = hist.sum()
    if total > 0:
        hist /= total
    return hist


def find_near_duplicates(input_dir, threshold, bins=256):
    """
    Cluster images in `input_dir` whose normalized grayscale histograms
    are within `threshold` L1 distance.

    Transitive grouping: if A~B and B~C, then {A, B, C} form one cluster
    even if A and C are farther apart than `threshold`.

    Args:
        input_dir: directory containing images (non-recursive).
        threshold: L1 distance cutoff in [0, 2]. Two normalized histograms
                   with L1 distance <= threshold are considered near-duplicates.
        bins: number of histogram bins (default 256 for 8-bit grayscale).

    Returns:
        List of clusters; each cluster is a list of file paths (sorted).
        Only clusters with 2+ members are returned, sorted by size desc.
    """
    # 1. Collect candidate image files
    paths = []
    for name in sorted(os.listdir(input_dir)):
        full = os.path.join(input_dir, name)
        if os.path.isfile(full) and os.path.splitext(name)[1].lower() in IMAGE_EXTS:
            paths.append(full)

    if len(paths) < 2:
        return []

    # 2. Compute normalized histograms
    hists = []
    valid_paths = []
    for p in paths:
        try:
            hists.append(_normalized_grayscale_histogram(p, bins=bins))
            valid_paths.append(p)
        except Exception as e:
            print(f"  skipping {p}: {e}")

    n = len(valid_paths)
    if n < 2:
        return []

    H = np.vstack(hists)  # (n, bins)

    # 3. Pairwise L1 distances (vectorized: |a-b| summed along bins)
    if _HAS_SCIPY:
        D = cdist(H, H, metric='cityblock')
    else:
        # Fallback: broadcasting (works, uses more memory for large n)
        D = np.abs(H[:, None, :] - H[None, :, :]).sum(axis=2)

    # 4. Union-find over pairs within threshold
    uf = UnionFind(n)
    # Only iterate upper triangle to avoid double work
    iu, ju = np.triu_indices(n, k=1)
    close = D[iu, ju] <= threshold
    for i, j in zip(iu[close], ju[close]):
        uf.union(int(i), int(j))

    # 5. Build clusters, keep only those with >= 2 members
    clusters = []
    for members in uf.groups().values():
        if len(members) >= 2:
            clusters.append(sorted(valid_paths[m] for m in members))

    clusters.sort(key=len, reverse=True)
    return clusters


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("usage: python find_near_duplicates.py <input_dir> <threshold> [bins]")
        sys.exit(1)

    input_dir = sys.argv[1]
    threshold = float(sys.argv[2])
    bins = int(sys.argv[3]) if len(sys.argv) > 3 else 256

    clusters = find_near_duplicates(input_dir, threshold, bins=bins)
    if not clusters:
        print("No near-duplicate clusters found.")
    else:
        for i, cluster in enumerate(clusters, 1):
            print(f"\nCluster {i} ({len(cluster)} images):")
            for p in cluster:
                print(f"  {p}")