from pathlib import Path
from PIL import Image
import numpy as np


def find_fuzzy_duplicates(input_dir, hash_size=8, max_hamming=5):
    """
    Find fuzzy/near-duplicate images using average-hash Hamming distance.

    Images are clustered transitively using union-find:
    if A is close to B and B is close to C, all three belong
    to the same cluster even if A and C are not directly close.

    Args:
        input_dir: Directory containing images.
        hash_size: Size of the square average hash.
        max_hamming: Maximum Hamming distance for two images to
                     be considered similar.

    Returns:
        A list of clusters, where each cluster is a list of image paths.
        Only clusters containing at least two images are returned.
    """
    if not isinstance(hash_size, int) or hash_size <= 0:
        raise ValueError("hash_size must be a positive integer")

    max_distance = hash_size * hash_size
    if not isinstance(max_hamming, int) or not 0 <= max_hamming <= max_distance:
        raise ValueError(
            f"max_hamming must be between 0 and {max_distance}"
        )

    input_dir = Path(input_dir)

    if not input_dir.is_dir():
        raise ValueError(f"Not a directory: {input_dir}")

    extensions = {
        ".jpg", ".jpeg", ".png", ".bmp",
        ".gif", ".tif", ".tiff", ".webp"
    }

    image_paths = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in extensions
    )

    if len(image_paths) < 2:
        return []

    def average_hash(path):
        with Image.open(path) as img:
            gray = img.convert("L").resize(
                (hash_size, hash_size),
                Image.Resampling.LANCZOS
            )
            pixels = np.asarray(gray, dtype=np.float32)
            average = pixels.mean()
            return pixels >= average

    # Compute hashes once.
    hashes = []
    valid_paths = []

    for path in image_paths:
        try:
            hashes.append(average_hash(path))
            valid_paths.append(path)
        except (OSError, ValueError):
            # Ignore files that cannot be decoded as images.
            continue

    n = len(valid_paths)

    if n < 2:
        return []

    # Union-find data structure.
    parent = list(range(n))
    rank = [0] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        root_a = find(a)
        root_b = find(b)

        if root_a == root_b:
            return

        if rank[root_a] < rank[root_b]:
            root_a, root_b = root_b, root_a

        parent[root_b] = root_a

        if rank[root_a] == rank[root_b]:
            rank[root_a] += 1

    # Connect every pair whose average hashes are within the threshold.
    for i in range(n):
        for j in range(i + 1, n):
            distance = np.count_nonzero(hashes[i] != hashes[j])

            if distance <= max_hamming:
                union(i, j)

    # Build transitive clusters.
    clusters = {}

    for i, path in enumerate(valid_paths):
        root = find(i)
        clusters.setdefault(root, []).append(str(path))

    # Only return actual duplicate groups.
    return [
        members
        for members in clusters.values()
        if len(members) >= 2
    ]