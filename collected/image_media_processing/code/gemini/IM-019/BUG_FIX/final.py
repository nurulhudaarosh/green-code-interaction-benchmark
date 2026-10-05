import os
from pathlib import Path
from PIL import Image

class UnionFind:
    """Disjoint Set Union (DSU) to handle transitive clustering."""
    def __init__(self):
        self.parent = {}

    def find(self, i):
        if i not in self.parent:
            self.parent[i] = i
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])  # Path compression
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j


def compute_ahash(image_path: Path, hash_size: int = 8) -> int:
    """Computes the Average Hash (aHash) of an image returned as an integer."""
    with Image.open(image_path) as img:
        # Convert to grayscale and resize to (hash_size, hash_size)
        img = img.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())
        
        # Calculate mean pixel value
        avg = sum(pixels) / len(pixels)
        
        # Build bit sequence: 1 if pixel >= avg, else 0
        diff = [1 if pixel >= avg else 0 for pixel in pixels]
        
        # Convert bit list to an integer bitmask
        hash_val = 0
        for bit in diff:
            hash_val = (hash_val << 1) | bit
            
        return hash_val


def hamming_distance(hash1: int, hash2: int) -> int:
    """Calculates Hamming distance using bitwise XOR and popcount."""
    return (hash1 ^ hash2).bit_count()


def find_fuzzy_duplicates(input_dir: str, hash_size: int = 8, max_hamming: int = 5) -> list[list[str]]:
    """
    Finds fuzzy duplicate images in input_dir using average-hash and 
    clusters them using transitive union-find grouping.
    
    :param input_dir: Path to directory containing images.
    :param hash_size: Size of the hash grid (e.g., 8 produces 8x8 = 64-bit hash).
    :param max_hamming: Maximum Hamming distance threshold to treat images as duplicates.
    :return: List of clusters, where each cluster is a list of file paths.
    """
    max_bits = hash_size * hash_size
    if not (0 <= max_hamming <= max_bits):
        raise ValueError(
            f"max_hamming ({max_hamming}) must be between 0 and {max_bits} for hash_size={hash_size}."
        )

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
    image_paths = []
    
    # Collect all image files
    for root, _, files in os.walk(input_dir):
        for file in files:
            path = Path(root) / file
            if path.suffix.lower() in valid_extensions:
                image_paths.append(path)

    if not image_paths:
        return []

    # Compute average hashes for all images
    hashes = {}
    for path in image_paths:
        try:
            hashes[path] = compute_ahash(path, hash_size=hash_size)
        except Exception as e:
            print(f"Skipping unreadable image {path}: {e}")

    paths = list(hashes.keys())
    uf = UnionFind()

    # Compare all pairs and union if distance <= max_hamming
    n = len(paths)
    for i in range(n):
        path1 = paths[i]
        hash1 = hashes[path1]
        for j in range(i + 1, n):
            path2 = paths[j]
            hash2 = hashes[path2]
            
            if hamming_distance(hash1, hash2) <= max_hamming:
                uf.union(path1, path2)

    # Group files by their union-find root
    clusters = {}
    for path in paths:
        root = uf.find(path)
        clusters.setdefault(root, []).append(str(path))

    # Return only clusters containing 2 or more files (actual duplicates)
    return [group for group in clusters.values() if len(group) > 1]