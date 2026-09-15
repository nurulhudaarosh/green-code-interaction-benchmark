import numpy as np
from PIL import Image


def compute_ahash(image_path: str, hash_size: int = 8) -> str:
    """Computes the Average Hash (aHash) of an image.

    Handles flat-color/uniform images consistently by setting tie-breaker to '>='.

    Args:
        image_path: Path to the image file.
        hash_size: Width and height of the resized image (default 8 for 64-bit
          hash).

    Returns:
        Hexadecimal string representation of the perceptual hash.
    """
    img = Image.open(image_path).convert("L")
    img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)

    pixels = np.array(img, dtype=np.float64)
    avg = pixels.mean()

    # Using '>=' breaks ties consistently for uniform/solid-color images:
    # Every pixel equals the mean, resulting in an all-1s hash ('ffffffffffffffff')
    diff = pixels >= avg

    bits = diff.flatten()
    byte_array = np.packbits(bits)
    return byte_array.tobytes().hex()


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Calculates the Hamming distance between two hex hashes.

    Args:
        hash_a: Hexadecimal hash string.
        hash_b: Hexadecimal hash string.

    Returns:
        The number of differing bits (0 means identical).
    """
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must be of equal length to compare.")

    bytes_a = bytes.fromhex(hash_a)
    bytes_b = bytes.fromhex(hash_b)

    distance = 0
    for byte1, byte2 in zip(bytes_a, bytes_b):
        distance += bin(byte1 ^ byte2).count("1")

    return distance