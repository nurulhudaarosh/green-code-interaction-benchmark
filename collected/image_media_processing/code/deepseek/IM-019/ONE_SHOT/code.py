import os
from pathlib import Path
from itertools import combinations
from PIL import Image


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", ".tif"}


def average_hash(path, hash_size=8):
    """Compute aHash as an integer (hash_size*hash_size bits)."""
    with Image.open(path) as img:
        img = img.convert("L").resize(
            (hash_size, hash_size), Image.Resampling.LANCZOS
        )
        pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)
    bits = 0
    for i, p in enumerate(pixels):
        if p >= avg:
            bits |= 1 << i
    return bits


def hamming(a, b):
    return (a ^ b).bit_count()


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        # path compression
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def find_fuzzy_duplicates(input_dir, hash_size=8, max_hamming=5):
    """
    Scan input_dir recursively for images, compute aHash for each, and group
    images whose Hamming distance is <= max_hamming using transitive union-find.

    Returns:
        List of clusters (each a list of file paths), only clusters with
        more than one member. Clusters are sorted by size (desc) then by
        first path.
    """
    input_dir = Path(input_dir)
    paths = [
        p for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]

    hashes = []
    valid_paths = []
    for p in paths:
        try:
            hashes.append(average_hash(p, hash_size))
            valid_paths.append(str(p))
        except Exception as e:
            print(f"[skip] {p}: {e}")

    n = len(valid_paths)
    uf = UnionFind(n)

    # O(n^2) pairwise comparison. For large n, swap in BK-tree / LSH.
    for i, j in combinations(range(n), 2):
        if hamming(hashes[i], hashes[j]) <= max_hamming:
            uf.union(i, j)

    groups = {}
    for i in range(n):
        groups.setdefault(uf.find(i), []).append(valid_paths[i])

    clusters = [g for g in groups.values() if len(g) > 1]
    clusters.sort(key=lambda g: (-len(g), g[0]))
    return clusters


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fuzzy_dupes.py <input_dir> [hash_size] [max_hamming]")
        sys.exit(1)

    d = sys.argv[1]
    hs = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    mh = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    for idx, cluster in enumerate(find_fuzzy_duplicates(d, hs, mh), 1):
        print(f"\nCluster {idx} ({len(cluster)} images):")
        for f in cluster:
            print(f"  {f}")