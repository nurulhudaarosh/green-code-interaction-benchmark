from itertools import combinations
import numpy as np
from PIL import Image


def compute_ahash(image_path: str, hash_size: int = 8) -> str:
    """Computes the average hash (aHash) for an image."""
    img = Image.open(image_path).convert("L")
    img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)

    pixels = np.asarray(img, dtype=np.float32)
    avg_pixel = pixels.mean()
    diff = pixels >= avg_pixel

    bits = diff.flatten()
    packed = np.packbits(bits)
    return "".join(f"{byte:02x}" for byte in packed)


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Calculates the Hamming distance between two hex-encoded hashes."""
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must be of equal length to compare.")

    bytes_a = bytes.fromhex(hash_a)
    bytes_b = bytes.fromhex(hash_b)

    return sum(bin(byte_a ^ byte_b).count("1") for byte_a, byte_b in zip(bytes_a, bytes_b))


def find_similar_pairs(image_paths: list[str], threshold: int = 10, hash_size: int = 8) -> list[tuple[str, str, int]]:
    """Finds all pairs of images whose Hamming distance is <= threshold.

    Args:
        image_paths: List of file paths to images.
        threshold: Maximum Hamming distance for images to be considered similar.
        hash_size: Size of the hash grid (default 8 for 64-bit hash).

    Returns:
        List of tuples: (image_path_a, image_path_b, distance)
    """
    # Precompute hashes once per image to avoid redundant file I/O and processing
    hashes = {}
    for path in image_paths:
        try:
            hashes[path] = compute_ahash(path, hash_size=hash_size)
        except Exception as e:
            print(f"Skipping {path}: {e}")

    similar_pairs = []

    # Iterate over all unique combinations of image pairs
    for (path_a, hash_a), (path_b, hash_b) in combinations(hashes.items(), 2):
        dist = hamming_distance(hash_a, hash_b)
        if dist <= threshold:
            similar_pairs.append((path_a, path_b, dist))

    return similar_pairs