from pathlib import Path
from PIL import Image


def _average_hash(image_path, hash_size=8):
    """Compute the average hash (aHash) of an image."""
    with Image.open(image_path) as img:
        gray = img.convert("L").resize((hash_size, hash_size))
        pixels = list(gray.getdata())
        avg = sum(pixels) / len(pixels)
        return [pixel >= avg for pixel in pixels]


def _hamming_distance(hash1, hash2):
    """Return the Hamming distance between two hashes."""
    return sum(a != b for a, b in zip(hash1, hash2))


def find_fuzzy_duplicates(input_dir, hash_size=8, max_hamming=5):
    """
    Cluster images by average-hash Hamming distance using transitive
    union-find grouping.

    Returns:
        list[list[str]]: Clusters containing at least two images.
    """
    if hash_size <= 0:
        raise ValueError("hash_size must be positive")

    # The hash contains hash_size * hash_size bits.
    max_hash_distance = hash_size * hash_size

    if not 0 <= max_hamming <= max_hash_distance:
        raise ValueError(
            f"max_hamming must be between 0 and "
            f"{max_hash_distance} for hash_size={hash_size}"
        )

    input_dir = Path(input_dir)
    image_extensions = {
        ".jpg", ".jpeg", ".png", ".bmp", ".gif",
        ".tif", ".tiff", ".webp"
    }

    image_paths = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in image_extensions
    )

    if len(image_paths) < 2:
        return []

    hashes = []
    valid_paths = []

    for path in image_paths:
        try:
            hashes.append(_average_hash(path, hash_size))
            valid_paths.append(path)
        except (OSError, ValueError):
            continue

    if len(valid_paths) < 2:
        return []

    # Union-find.
    parent = list(range(len(valid_paths)))
    rank = [0] * len(valid_paths)

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
            parent[root_a] = root_b
        elif rank[root_a] > rank[root_b]:
            parent[root_b] = root_a
        else:
            parent[root_b] = root_a
            rank[root_a] += 1

    # Build similarity connections.
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            if _hamming_distance(hashes[i], hashes[j]) <= max_hamming:
                union(i, j)

    # Resolve transitive clusters.
    clusters = {}

    for i, path in enumerate(valid_paths):
        root = find(i)
        clusters.setdefault(root, []).append(str(path))

    return [
        members
        for members in clusters.values()
        if len(members) >= 2
    ]