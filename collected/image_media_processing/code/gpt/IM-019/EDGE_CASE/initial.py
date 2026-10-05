from pathlib import Path
from PIL import Image


def _average_hash(image_path, hash_size=8):
    """Return the average hash as an integer."""
    with Image.open(image_path) as img:
        gray = img.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)

        pixels = list(gray.getdata())
        avg = sum(pixels) / len(pixels)

        hash_value = 0
        for pixel in pixels:
            hash_value = (hash_value << 1) | (1 if pixel >= avg else 0)

        return hash_value


def _hamming_distance(hash1, hash2):
    """Return the Hamming distance between two integer hashes."""
    return (hash1 ^ hash2).bit_count()


def find_fuzzy_duplicates(input_dir, hash_size=8, max_hamming=5):
    """
    Cluster images by average-hash Hamming distance using transitive
    union-find grouping.

    Args:
        input_dir: Directory containing images.
        hash_size: Width/height of the average hash.
        max_hamming: Maximum Hamming distance for two images to be
                     considered similar.

    Returns:
        List of clusters, where each cluster is a list of filenames.
        Only clusters containing at least two images are returned.
    """
    if not isinstance(hash_size, int) or hash_size <= 0:
        raise ValueError("hash_size must be a positive integer")

    if not isinstance(max_hamming, int) or not 0 <= max_hamming <= hash_size * hash_size:
        raise ValueError(
            f"max_hamming must be between 0 and {hash_size * hash_size}"
        )

    input_dir = Path(input_dir)

    if not input_dir.is_dir():
        raise ValueError(f"Not a directory: {input_dir}")

    image_extensions = {
        ".jpg", ".jpeg", ".png", ".bmp", ".gif",
        ".tif", ".tiff", ".webp"
    }

    image_paths = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in image_extensions
    )

    # Compute hashes, skipping files Pillow cannot open.
    hashes = []
    for path in image_paths:
        try:
            hash_value = _average_hash(path, hash_size)
            hashes.append((path.name, hash_value))
        except (OSError, ValueError):
            continue

    n = len(hashes)

    if n < 2:
        return []

    # Union-Find / Disjoint Set Union.
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

    # Connect every pair that is within the threshold.
    for i in range(n):
        for j in range(i + 1, n):
            if _hamming_distance(hashes[i][1], hashes[j][1]) <= max_hamming:
                union(i, j)

    # Build transitive clusters.
    clusters = {}

    for i, (filename, _) in enumerate(hashes):
        root = find(i)
        clusters.setdefault(root, []).append(filename)

    # A duplicate cluster must contain at least two images.
    return [
        cluster
        for cluster in clusters.values()
        if len(cluster) >= 2
    ]