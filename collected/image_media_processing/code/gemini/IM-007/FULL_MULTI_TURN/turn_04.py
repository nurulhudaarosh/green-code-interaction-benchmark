from itertools import combinations
import numpy as np
from PIL import Image


def compute_ahash(image_path: str, hash_size: int = 8) -> str:
    """Computes the average-hash (aHash) of an image using dynamic mean.

    Handles flat-color (uniform) images gracefully by evaluating pixels >= mean
    to True, resulting in a consistent all-1s hash.

    Args:

        image_path: Path to the image file.
        hash_size: Grid size for hash (default 8 yields 64 bits / 16 hex chars).

    Returns:

        Hexadecimal string of the perceptual hash.
    """
    img = Image.open(image_path).convert("L")
    img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    pixels = np.array(img, dtype=np.float64)

    pixel_mean = np.mean(pixels)

    # If all pixels are identical (flat image), pixel_mean equals pixel values.
    # `>=` breaks ties consistently towards True (1), producing an all-1s hash.
    diff = pixels >= pixel_mean

    # Convert 2D boolean array into packed 8-bit hex representation
    packed_bytes = np.packbits(diff.flatten())
    return "".join(f"{byte:02x}" for byte in packed_bytes)


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Calculates the number of differing bits between two hexadecimal hashes."""
    if len(hash_a) != len(hash_b):
        raise ValueError(
            f"Hash length mismatch: {len(hash_a)} vs {len(hash_b)}"
        )

    val_a = int(hash_a, 16)
    val_b = int(hash_b, 16)
    return (val_a ^ val_b).bit_count()


def find_similar_pairs(
    image_paths: list[str], threshold: int = 10, hash_size: int = 8
) -> list[tuple[str, str, int]]:
    """Finds all unordered pairs of images with Hamming distance <= threshold.

    Args:

        image_paths: List of file paths to process.
        threshold: Maximum bit difference for images to be considered similar.
        hash_size: Grid size used during hash computation.

    Returns:

        List of tuples: (path_1, path_2, distance)
    """
    hashes = {}
    for path in image_paths:
        try:
            hashes[path] = compute_ahash(path, hash_size=hash_size)
        except Exception as err:
            print(f"Skipping {path}: {err}")

    similar_pairs = []
    for (path_a, hash_a), (path_b, hash_b) in combinations(hashes.items(), 2):
        dist = hamming_distance(hash_a, hash_b)
        if dist <= threshold:
            similar_pairs.append((path_a, path_b, dist))

    return similar_pairs