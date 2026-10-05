import os
from pathlib import Path
from collections import defaultdict
from PIL import Image


def _average_hash(image_path, hash_size=8):
    """Compute the average hash (aHash) of an image as an integer.
    
    The image is converted to grayscale, resized to (hash_size, hash_size),
    and each pixel is compared to the mean. Bits above the mean are 1.
    """
    with Image.open(image_path) as img:
        img = img.convert("L").resize((hash_size, hash_size), Image.LANCZOS)
        pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)
    bits = 0
    for i, p in enumerate(pixels):
        if p >= avg:
            bits |= 1 << i
    return bits


def _hamming(a, b):
    """Number of differing bits between two integers."""
    return bin(a ^ b).count("1")


class _UnionFind:
    """Standard union-find with path compression and union by rank."""
    
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


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}


def find_fuzzy_duplicates(input_dir, hash_size=8, max_hamming=5):
    """Cluster images in `input_dir` by average-hash Hamming distance.

    Two images are considered "similar" if the Hamming distance between their
    average hashes is <= max_hamming. Similarity is treated as transitive:
    if A~B and B~C, then {A, B, C} form one cluster even if A and C are far
    apart. Uses union-find for efficient transitive grouping.

    Args:
        input_dir: Directory to scan (non-recursive).
        hash_size: Side length of the downscaled hash grid (default 8 -> 64 bits).
        max_hamming: Max Hamming distance to consider two images similar.

    Returns:
        A list of clusters. Each cluster is a list of file paths (str).
        Only clusters with 2+ members are returned; singletons are dropped.
        Clusters are sorted by size (descending), and paths within a cluster
        are sorted for deterministic output.

        Edge cases:
          - Empty directory or no valid images -> [].
          - Exactly one valid image -> [] (no pairs exist to compare, so
            there can be no cluster of size >= 2).
          - All images unreadable/corrupt -> [].
    """
    input_path = Path(input_dir)
    if not input_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    # 1. Collect image files and compute hashes.
    paths = []
    hashes = []
    for entry in sorted(input_path.iterdir()):
        if entry.is_file() and entry.suffix.lower() in IMAGE_EXTENSIONS:
            try:
                h = _average_hash(entry, hash_size)
            except Exception:
                # Skip unreadable / corrupt images.
                continue
            paths.append(str(entry))
            hashes.append(h)

    n = len(paths)

    # 2. Early return for 0 or 1 images.
    #    With fewer than 2 images there are no pairs to compare, and a
    #    single image can never form a cluster of size >= 2. Returning []
    #    here also avoids constructing a union-find and running the
    #    O(n^2) pairwise loop unnecessarily.
    if n < 2:
        return []

    # 3. Union-find: compare every pair, union when Hamming <= max_hamming.
    #    For small datasets the O(n^2) pairwise scan is fine. For larger sets
    #    you'd want BK-tree / LSH bucketing on the hash bits.
    uf = _UnionFind(n)
    for i in range(n):
        hi = hashes[i]
        for j in range(i + 1, n):
            if _hamming(hi, hashes[j]) <= max_hamming:
                uf.union(i, j)

    # 4. Group paths by their root representative.
    groups = defaultdict(list)
    for idx in range(n):
        groups[uf.find(idx)].append(paths[idx])

    # 5. Drop singletons, sort for deterministic output.
    clusters = [sorted(members) for members in groups.values() if len(members) > 1]
    clusters.sort(key=lambda c: (-len(c), c[0]))
    return clusters


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    result = find_fuzzy_duplicates(target)
    for i, cluster in enumerate(result, 1):
        print(f"Cluster {i} ({len(cluster)} images):")
        for p in cluster:
            print(f"  {p}")