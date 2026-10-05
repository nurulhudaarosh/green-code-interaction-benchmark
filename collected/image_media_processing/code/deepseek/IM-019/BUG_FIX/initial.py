import os
from pathlib import Path
from PIL import Image
import numpy as np


# ---------- Union-Find (Disjoint Set Union) ----------

class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        # Path compression
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        # Union by rank
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


# ---------- Average hash ----------

def average_hash(path, hash_size=8):
    """Compute the average hash (aHash) of an image as a bit array.

    Returns a 1-D numpy array of dtype uint8 with length hash_size**2,
    or None if the image cannot be read.
    """
    try:
        with Image.open(path) as img:
            img = img.convert("L").resize(
                (hash_size, hash_size), Image.LANCZOS
            )
            pixels = np.asarray(img, dtype=np.float64)
    except Exception:
        return None

    avg = pixels.mean()
    return (pixels > avg).astype(np.uint8).flatten()


def hamming_distance(h1, h2):
    """Hamming distance between two equal-length bit arrays."""
    return int(np.count_nonzero(h1 != h2))


# ---------- Main function ----------

def find_fuzzy_duplicates(input_dir, hash_size=8, max_hamming=5):
    """Cluster images in `input_dir` by aHash Hamming distance.

    Two images are linked if their Hamming distance is <= max_hamming.
    Clusters are formed by transitive closure (union-find), so an image
    joins a cluster if it is within `max_hamming` of *any* member.

    Parameters
    ----------
    input_dir : str | os.PathLike
        Directory to scan (recursively) for image files.
    hash_size : int
        Side length of the downsampled hash grid. Hash length = hash_size**2.
    max_hamming : int
        Maximum Hamming distance for two images to be considered similar.

    Returns
    -------
    list[list[str]]
        A list of clusters; each cluster is a list of file paths.
        Only clusters with >= 2 members are returned, sorted by
        descending cluster size.
    """
    if hash_size < 1:
        raise ValueError("hash_size must be >= 1")
    if not (0 <= max_hamming <= hash_size ** 2):
        raise ValueError(
            f"max_hamming must be in [0, {hash_size ** 2}]"
        )

    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    # --- Collect candidate image files ---
    image_exts = {
        ".jpg", ".jpeg", ".png", ".bmp", ".gif",
        ".tif", ".tiff", ".webp",
    }
    paths = [
        str(p)
        for p in sorted(input_dir.rglob("*"))
        if p.is_file() and p.suffix.lower() in image_exts
    ]

    # --- Compute hashes ---
    entries = []  # (path, hash_array)
    for p in paths:
        h = average_hash(p, hash_size=hash_size)
        if h is not None:
            entries.append((p, h))

    n = len(entries)
    if n < 2:
        return []

    # --- Compare all pairs, union those within threshold ---
    # Pack each hash into a Python int for fast Hamming distance via bit ops.
    packed = []
    for _, h in entries:
        bits = 0
        for b in h:
            bits = (bits << 1) | int(b)
        packed.append(bits)

    uf = UnionFind(n)

    # All-pairs comparison. For very large directories, consider an
    # LSH index (e.g., BK-tree or random-projection buckets) to avoid O(n^2).
    for i in range(n):
        hi = packed[i]
        for j in range(i + 1, n):
            # int.bit_count() is available on Python 3.10+;
            # use bin(x).count("1") as a fallback.
            diff = hi ^ packed[j]
            try:
                dist = diff.bit_count()
            except AttributeError:
                dist = bin(diff).count("1")
            if dist <= max_hamming:
                uf.union(i, j)

    # --- Gather clusters ---
    clusters = {}
    for idx in range(n):
        root = uf.find(idx)
        clusters.setdefault(root, []).append(entries[idx][0])

    result = [members for members in clusters.values() if len(members) > 1]
    result.sort(key=len, reverse=True)
    return result


# ---------- Example usage ----------

if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    groups = find_fuzzy_duplicates(target, hash_size=8, max_hamming=5)
    if not groups:
        print("No fuzzy duplicates found.")
    for i, group in enumerate(groups, 1):
        print(f"\nCluster {i} ({len(group)} images):")
        for path in group:
            print(f"  {path}")