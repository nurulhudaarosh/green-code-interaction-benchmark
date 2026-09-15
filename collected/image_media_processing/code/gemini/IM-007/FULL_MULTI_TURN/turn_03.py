from itertools import combinations
import numpy as np
from PIL import Image


def compute_ahash(image_path: str, hash_size: int = 8) -> str:
    """Computes average-hash (aHash) using the dynamic mean of the resized pixels."""
    img = Image.open(image_path).convert("L")
    img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    pixels = np.array(img, dtype=np.float64)

    pixel_mean = np.mean(pixels)
    diff = pixels >= pixel_mean

    packed_bytes = np.packbits(diff.flatten())
    return "".join(f"{byte:02x}" for byte in packed_bytes)


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Calculates bitwise differences between two hex hashes."""
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must be of equal length to compare.")

    val_a = int(hash_a, 16)
    val_b = int(hash_b, 16)
    return (val_a ^ val_b).bit_count()


def find_similar_pairs(
    image_paths: list[str], threshold: int = 10, hash_size: int = 8
) -> list[tuple[str, str, int]]:
    """Finds all pairs of images whose Hamming distance is <= threshold.

    Args:

        image_paths: List of file paths to images.
        threshold: Maximum Hamming distance to consider two images similar.
        hash_size: Grid size used during hash computation.

    Returns:

        A list of tuples: (image_path_1, image_path_2, distance).
    """
    # 1. Precompute hashes once per image to avoid redundant calculations
    hashes = {}
    for path in image_paths:
        try:
            hashes[path] = compute_ahash(path, hash_size=hash_size)
        except Exception as e:
            print(f"Warning: Could not compute hash for {path}: {e}")

    similar_pairs = []

    # 2. Iterate over all unique unordered pairs (O(N^2 / 2))
    for (path_a, hash_a), (path_b, hash_b) in combinations(hashes.items(), 2):
        dist = hamming_distance(hash_a, hash_b)
        if dist <= threshold:
            similar_pairs.append((path_a, path_b, dist))

    return similar_pairs


# Example Usage
if __name__ == "__main__":
    images = [
        "images/photo1.jpg",
        "images/photo1_resized.jpg",
        "images/photo2.jpg",
        "images/photo3.jpg",
    ]

    # Find pairs with 10 or fewer bit differences
    matches = find_similar_pairs(images, threshold=10)

    for img1, img2, dist in matches:
        print(f"Match found! {img1} <-> {img2} (Distance: {dist})")