from pathlib import Path
from PIL import Image
import numpy as np


def find_fuzzy_duplicates(
    input_dir,
    hash_size=8,
    max_hamming=5,
    return_hashes=False,
):
    """
    Find fuzzy/near-duplicate images using average-hash Hamming distance.

    Args:
        input_dir: Directory containing images.
        hash_size: Size of the square average hash.
        max_hamming: Maximum Hamming distance for two images to be
                     considered similar.
        return_hashes: If True, return (clusters, hash_map), where
                       hash_map maps filenames to integer hashes.

    Returns:
        If return_hashes=False:
            List of duplicate clusters.

        If return_hashes=True:
            (clusters, hash_map)
    """
    if not isinstance(hash_size, int) or hash_size <= 0:
        raise ValueError("hash_size must be a positive integer")

    max_distance = hash_size * hash_size

    if not isinstance(max_hamming, int) or not 0 <= max_hamming <= max_distance:
        raise ValueError(
            f"max_hamming must be between 0 and {max_distance}"
        )

    if not isinstance(return_hashes, bool):
        raise ValueError("return_hashes must be a boolean")

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
        return ([], {}) if return_hashes else []

    def average_hash(path):
        with Image.open(path) as img:
            gray = img.convert("L").resize(
                (hash_size, hash_size),
                Image.Resampling.LANCZOS
            )
            pixels = np.asarray(gray, dtype=np.float32)
            average = pixels.mean()

            bits = pixels >= average

            # Convert the boolean hash into one integer.
            value = 0
            for bit in bits.flat:
                value = (value << 1) | int(bit)

            return value

    hashes = []
    valid_paths = []
    hash_map = {}

    for path in image_paths:
        try:
            image_hash = average_hash(path)
            hashes.append(image_hash)
            valid_paths.append(path)

            # Map filename, rather than the complete path.
            hash_map[path.name] = image_hash

        except (OSError, ValueError):
            # Ignore files that cannot be decoded as images.
            continue

    n = len(valid_paths)

    if n < 2:
        return ([], hash_map) if return_hashes else []

    # Union-find.
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

    # Compare integer hashes using XOR + bit count.
    for i in range(n):
        for j in range(i + 1, n):
            distance = (hashes[i] ^ hashes[j]).bit_count()

            if distance <= max_hamming:
                union(i, j)

    # Build transitive clusters.
    clusters = {}

    for i, path in enumerate(valid_paths):
        root = find(i)
        clusters.setdefault(root, []).append(str(path))

    # Only retain clusters with at least two members.
    result = [
        members
        for members in clusters.values()
        if len(members) >= 2
    ]

    if return_hashes:
        return result, hash_map

    return result