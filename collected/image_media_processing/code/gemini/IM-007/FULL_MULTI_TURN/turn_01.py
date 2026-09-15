import numpy as np
from PIL import Image


def compute_ahash(image_path: str, hash_size: int = 8) -> str:
    """Computes the average-hash (aHash) of an image.

    Args:

        image_path: Path to the image file.
        hash_size: The grid size for the hash (default 8 produces a 64-bit
          hash).

    Returns:

        A hexadecimal string representation of the perceptual hash.
    """
    # 1. Open image and convert to grayscale ('L')
    img = Image.open(image_path).convert("L")

    # 2. Resize using high-quality anti-aliasing (LANCZOS or Resampling.LANCZOS)
    img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)

    # 3. Convert image pixels to a numpy array
    pixels = np.array(img, dtype=np.float64)

    # 4. Compute the average pixel value
    avg = pixels.mean()

    # 5. Create a boolean mask: True where pixel >= mean, False otherwise
    diff = pixels >= avg

    # 6. Convert the boolean array to a hexadecimal string
    # Pack bits into uint8 bytes and convert to hex
    packed_bytes = np.packbits(diff.flatten())
    hex_hash = "".join(f"{byte:02x}" for byte in packed_bytes)

    return hex_hash


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Calculates the Hamming distance (number of differing bits) between two hex

    hashes.

    Args:

        hash_a: Hexadecimal hash string.
        hash_b: Hexadecimal hash string.

    Returns:

        Integer representing the number of bit differences.
    """
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must be of equal length to compare.")

    # Convert hex strings to integer bitmasks and XOR them
    val_a = int(hash_a, 16)
    val_b = int(hash_b, 16)

    # XOR yields 1 where bits differ; bit_count() counts set bits (Python 3.10+)
    return (val_a ^ val_b).bit_count()


# Example Usage
if __name__ == "__main__":
    # Generate hashes
    hash1 = compute_ahash("image1.jpg", hash_size=8)
    hash2 = compute_ahash("image2.jpg", hash_size=8)

    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")

    # Compute distance
    dist = hamming_distance(hash1, hash2)
    print(f"Hamming Distance: {dist}")

    # Distance interpretation threshold guide:
    # 0 = identical or near-identical image
    # <= 10 = highly likely to be visually similar or resized/recompressed versions
    # > 10 = distinct images