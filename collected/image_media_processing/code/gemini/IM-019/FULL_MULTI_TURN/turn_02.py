import os
from collections import defaultdict
from pathlib import Path
from PIL import Image
import imagehash


class UnionFind:
    """Disjoint-set data structure with path compression and union by rank."""
    def __init__(self, elements):
        self.parent = {el: el for el in elements}
        self.rank = {el: 0 for el in elements}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x != root_y:
            if self.rank[root_x] < self.rank[root_y]:
                root_x, root_y = root_y, root_x
            self.parent[root_y] = root_x
            if self.rank[root_x] == self.rank[root_y]:
                self.rank[root_x] += 1


def find_fuzzy_duplicates(input_dir: str, hash_size: int = 8, max_hamming: int = 5) -> list[list[str]]:
    """
    Finds fuzzy duplicate images in input_dir by computing average hash (aHash)
    and clustering them using Union-Find based on Hamming distance.

    :param input_dir: Path to directory containing images.
    :param hash_size: The side length of the hash grid (default 8 -> 64-bit hash).
    :param max_hamming: Maximum Hamming distance to consider images as duplicates.
    :return: List of clusters, where each cluster is a list of image file paths.
    """
    # Dynamic upper bound based on total hash bit size
    max_possible_distance = hash_size * hash_size

    if max_hamming < 0 or max_hamming > max_possible_distance:
        raise ValueError(
            f"max_hamming must be between 0 and {max_possible_distance} "
            f"for a hash_size of {hash_size}."
        )

    input_path = Path(input_dir)
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
    
    hashes = {}
    
    # 1. Compute average hash for all valid images in the directory
    for path in input_path.rglob("*"):
        if path.is_file() and path.suffix.lower() in valid_extensions:
            try:
                with Image.open(path) as img:
                    hashes[str(path)] = imagehash.average_hash(img, hash_size=hash_size)
            except Exception as e:
                print(f"Skipping corrupt or unreadable image {path}: {e}")

    paths = list(hashes.keys())
    uf = UnionFind(paths)

    # 2. Pairwise comparison and Union-Find merging
    n = len(paths)
    for i in range(n):
        for j in range(i + 1, n):
            path_a, path_b = paths[i], paths[j]
            distance = hashes[path_a] - hashes[path_b]
            
            if distance <= max_hamming:
                uf.union(path_a, path_b)

    # 3. Group files by their root representative
    clusters_map = defaultdict(list)
    for path in paths:
        root = uf.find(path)
        clusters_map[root].append(path)

    # 4. Return clusters with at least 2 duplicates
    duplicate_clusters = [cluster for cluster in clusters_map.values() if len(cluster) > 1]
    
    return duplicate_clusters