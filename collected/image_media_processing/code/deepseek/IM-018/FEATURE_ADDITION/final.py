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


def _l1_distances_from_row(H, i):
    """L1 distances between H[i] and every row H[j] for j > i."""
    return np.abs(H[i + 1:] - H[i]).sum(axis=1)


def _chi_squared_distances_from_row(H, i, eps=1e-12):
    """
    Chi-squared distances between H[i] and every row H[j] for j > i.

        d(p, q) = 0.5 * sum_k (p_k - q_k)^2 / (p_k + q_k + eps)

    The 0.5 factor keeps the result in [0, 1] for L1-normalized histograms,
    matching the range of the L1 distance.
    """
    p = H[i]
    Q = H[i + 1:]                             # shape (m, bins)
    diff = p - Q
    denom = p + Q + eps
    return 0.5 * np.sum((diff * diff) / denom, axis=1)


# Registry mapping metric name -> callable(H, i) -> distances to rows j > i.
_METRIC_FUNCS = {
    "l1": _l1_distances_from_row,
    "chi_squared": _chi_squared_distances_from_row,
}


def find_near_duplicates(input_dir, threshold, distance_metric="l1"):
    """
    Cluster images in `input_dir` by histogram distance. Two images are
    neighbors if the chosen distance between their L1-normalized grayscale
    histograms is <= threshold. Groups are formed by transitive closure
    (union-find), so A~B and B~C puts A, B, C in one cluster.

    Args:
        input_dir: Directory containing images (searched non-recursively).
        threshold: Maximum distance to consider near-duplicates.
            For 'l1', distance lies in [0, 2].
            For 'chi_squared', distance lies in [0, 1].
        distance_metric: 'l1' (default) or 'chi_squared'.

    Returns:
        List of clusters; each cluster is a sorted list of file paths.
        Singleton clusters (no duplicates found) are excluded.

    Raises:
        ValueError: If `distance_metric` is not recognized.
    """
    metric_fn = _METRIC_FUNCS.get(distance_metric)
    if metric_fn is None:
        raise ValueError(
            f"Unknown distance_metric {distance_metric!r}; "
            f"expected one of {sorted(_METRIC_FUNCS)}"
        )

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

    H = np.vstack(hists)                 # shape (n, bins)
    uf = _UnionFind(n)

    for i in range(n - 1):
        distances = metric_fn(H, i)
        for j_offset in np.nonzero(distances <= threshold)[0]:
            uf.union(i, i + 1 + int(j_offset))

    groups = defaultdict(list)
    for idx, path in enumerate(paths):
        groups[uf.find(idx)].append(path)

    clusters = [sorted(members) for members in groups.values() if len(members) > 1]
    clusters.sort(key=lambda c: c[0])
    return clusters


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Find near-duplicate images by histogram distance."
    )
    parser.add_argument("input_dir")
    parser.add_argument("threshold", type=float)
    parser.add_argument(
        "--metric",
        choices=sorted(_METRIC_FUNCS),
        default="l1",
        help="Distance metric (default: l1).",
    )
    args = parser.parse_args()

    for cluster in find_near_duplicates(args.input_dir, args.threshold, args.metric):
        print("Cluster:")
        for p in cluster:
            print("  ", p)