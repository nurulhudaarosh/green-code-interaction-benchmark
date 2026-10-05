import os
from collections import defaultdict
from PIL import Image

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(x, **kwargs):
        return x


def _average_hash(path, hash_size=8):
    """Compute average hash of an image as an integer bit pattern."""
    with Image.open(path) as img:
        img = img.convert("L").resize((hash_size, hash_size), Image.LANCZOS)
        pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)
    bits = 0
    for i, p in enumerate(pixels):
        if p >= avg:
            bits |= (1 << i)
    return bits


def _hamming(a, b):
    return bin(a ^ b).count("1")


class _UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        # Path compression (iterative)
        root = x
        while self.parent.get(root, root) != root:
            root = self.parent[root]
        while self.parent.get(x, x) != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x


def find_fuzzy_duplicates(input_dir, hash_size=8, max_hamming=5):
    """
    Cluster images in input_dir by average-hash Hamming distance.

    Two images are considered "similar" if their aHash Hamming distance is
    <= max_hamming. Clusters are formed via transitive closure using a
    union-find structure.

    Args:
        input_dir: Directory containing image files.
        hash_size: Side length of the square aHash (default 8 -> 64 bits).
        max_hamming: Max Hamming distance to consider two hashes similar.

    Returns:
        List of clusters (each a list of file paths). Only clusters with
        >= 2 members are returned. Clusters sorted by descending size.
    """
    if max_hamming < 0:
        raise ValueError("max_hamming must be non-negative")

    extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}

    hashes = {}   # path -> hash int
    failures = [] # (path, error)
    paths = []

    for name in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, name)
        if not os.path.isfile(path):
            continue
        if os.path.splitext(name)[1].lower() not in extensions:
            continue
        try:
            hashes[path] = _average_hash(path, hash_size=hash_size)
            paths.append(path)
        except Exception as e:
            failures.append((path, str(e)))

    uf = _UnionFind()
    for p in paths:
        uf.add(p)

    # Brute-force pairwise comparison. For very large directories, replace
    # with BK-tree or LSH bucketing.
    n = len(paths)
    iterator = tqdm(range(n), desc="Comparing hashes", disable=(n < 200))
    for i in iterator:
        hi = hashes[paths[i]]
        for j in range(i + 1, n):
            if _hamming(hi, hashes[paths[j]]) <= max_hamming:
                uf.union(paths[i], paths[j])

    clusters_map = defaultdict(list)
    for p in paths:
        clusters_map[uf.find(p)].append(p)

    clusters = [sorted(group) for group in clusters_map.values() if len(group) >= 2]
    clusters.sort(key=len, reverse=True)

    if failures:
        import warnings
        warnings.warn(
            f"Skipped {len(failures)} unreadable file(s); "
            f"first: {failures[0][0]} ({failures[0][1]})"
        )

    return clusters


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fuzzhash.py <input_dir> [hash_size] [max_hamming]")
        sys.exit(1)
    directory = sys.argv[1]
    hs = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    mh = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    groups = find_fuzzy_duplicates(directory, hash_size=hs, max_hamming=mh)
    print(f"\nFound {len(groups)} fuzzy-duplicate cluster(s).")
    for idx, group in enumerate(groups, 1):
        print(f"\nCluster {idx} ({len(group)} images):")
        for p in group:
            print(f"  {p}")