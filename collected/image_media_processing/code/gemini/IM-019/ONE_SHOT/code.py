import os
from pathlib import Path
from collections import defaultdict
from PIL import Image

class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, item):
        if item not in self.parent:
            self.parent[item] = item
            return item
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])  # Path compression
        return self.parent[item]

    def union(self, item1, item2):
        root1 = self.find(item1)
        root2 = self.find(item2)
        if root1 != root2:
            self.parent[root2] = root1

def compute_ahash(image_path, hash_size=8):
    """Computes the 64-bit Average Hash (aHash) for an image."""
    try:
        with Image.open(image_path) as img:
            # Convert to grayscale and resize to hash_size x hash_size using anti-aliasing
            img = img.convert('L').resize((hash_size, hash_size), Image.Resampling.LANCZOS)
            pixels = list(img.getdata())
            
            # Calculate average pixel value
            avg = sum(pixels) / len(pixels)
            
            # Construct bitmask based on whether pixel is above average
            hash_val = 0
            for pixel in pixels:
                hash_val = (hash_val << 1) | (1 if pixel >= avg else 0)
            return hash_val
    except Exception as e:
        # Ignore unreadable/corrupt image files or non-image formats
        return None

def hamming_distance(hash1, hash2):
    """Calculates the Hamming distance (number of differing bits) between two integer hashes."""
    return bin(hash1 ^ hash2).count('1')

def find_fuzzy_duplicates(input_dir, hash_size=8, max_hamming=5, valid_extensions=('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')):
    """
    Finds and clusters near-duplicate images in a directory using Average Hashing 
    and Transitive Union-Find grouping.
    
    :param input_dir: Path to directory containing images
    :param hash_size: Grid dimensions for aHash (e.g., 8 produces an 8x8 = 64-bit hash)
    :param max_hamming: Maximum Hamming distance threshold for considering two images duplicates
    :return: List of lists, where each sublist contains absolute path strings of connected duplicates
    """
    input_path = Path(input_dir)
    if not input_path.is_dir():
        raise ValueError(f"Directory non-existent or inaccessible: {input_dir}")

    # 1. Collect and hash all valid images
    hashes = {}
    for entry in input_path.rglob('*'):
        if entry.is_file() and entry.suffix.lower() in valid_extensions:
            h = compute_ahash(entry, hash_size=hash_size)
            if h is not None:
                hashes[str(entry.resolve())] = h

    file_paths = list(hashes.keys())
    uf = UnionFind()

    # Initialize all items in Union-Find
    for path in file_paths:
        uf.find(path)

    # 2. Pairwise comparison to find near-duplicates
    n = len(file_paths)
    for i in range(n):
        path1 = file_paths[i]
        hash1 = hashes[path1]
        for j in range(i + 1, n):
            path2 = file_paths[j]
            hash2 = hashes[path2]
            
            if hamming_distance(hash1, hash2) <= max_hamming:
                uf.union(path1, path2)

    # 3. Group by connected component root
    clusters = defaultdict(list)
    for path in file_paths:
        root = uf.find(path)
        clusters[root].append(path)

    # Filter out singletons (images with no duplicates)
    duplicate_groups = [group for group in clusters.values() if len(group) > 1]

    return duplicate_groups

# Example usage:
if __name__ == '__main__':
    # duplicates = find_fuzzy_duplicates("./my_photos", hash_size=8, max_hamming=5)
    # for idx, group in enumerate(duplicates, 1):
    #     print(f"Cluster {idx}: {group}")
    pass