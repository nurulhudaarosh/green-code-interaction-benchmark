from pathlib import Path
from PIL import Image


def _average_hash(image_path, hash_size=8):
    """Return the average hash as an integer."""
    with Image.open(image_path) as img:
        gray = img.convert("L").resize((hash_size, hash_size))
        pixels = list(gray.getdata())

    average = sum(pixels) / len(pixels)

    value = 0
    for pixel in pixels:
        value = (value << 1) | int(pixel >= average)

    return value


def _hamming_distance(hash1, hash2):
    """Return the Hamming distance between two integer hashes."""
    return (hash1 ^ hash2).bit_count()


def find_fuzzy_duplicates(input_dir, hash_size=8, max_hamming=5):
    """
    Cluster images using average-hash Hamming distance.

    Args:
        input_dir: Directory containing images.
        hash_size: Width and height of the average hash.
        max_hamming: Maximum allowed Hamming distance.

    Returns:
        A list of clusters, with each cluster containing at least
        two filenames.
    """
    if not isinstance(hash_size, int) or hash_size <= 0:
        raise ValueError("hash_size must be a positive integer")

    # The hash contains hash_size * hash_size bits.
    max_hash_distance = hash_size * hash_size

    if (
        not isinstance(max_hamming, int)
        or not 0 <= max_hamming <= max_hash_distance
    ):
        raise ValueError(
            f"max_hamming must be an integer between "
            f"0 and {max_hash_distance}"
        )

    input_path = Path(input_dir)
    if not input_path.is_dir():
        raise ValueError(f"Not a directory: {input_dir}")

    valid_extensions = {
        ".jpg", ".jpeg", ".png", ".bmp",
        ".gif", ".tif", ".tiff", ".webp"
    }

    image_paths = sorted(
        path
        for path in input_path.iterdir()
        if path.is_file() and path.suffix.lower() in valid_extensions
    )

    if len(image_paths) < 2:
        return []

    hashes = []

    for path in image_paths:
        try:
            image_hash = _average_hash(path, hash_size)
            hashes.append((path.name, image_hash))
        except (OSError, ValueError):
            continue

    if len(hashes) < 2:
        return []

    n = len(hashes)

    # Union-find.
    parent = list(range(n))
    rank = [0] * n

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

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

    # Connect similar images.
    for i in range(n):
        for j in range(i + 1, n):
            distance = _hamming_distance(
                hashes[i][1],
                hashes[j][1]
            )

            if distance <= max_hamming:
                union(i, j)

    # Build transitive clusters.
    clusters = {}

    for i, (filename, _) in enumerate(hashes):
        root = find(i)
        clusters.setdefault(root, []).append(filename)

    return [
        members
        for members in clusters.values()
        if len(members) >= 2
    ]