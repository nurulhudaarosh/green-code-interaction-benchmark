import numpy as np
from PIL import Image


def compute_ahash(image_path: str, hash_size: int = 8) -> str:
    """Computes average-hash (aHash) using the dynamic mean of the resized pixels.

    Args:

        image_path: Path to the image file.
        hash_size: Grid size for resizing (default 8 produces an 8x8 = 64-bit
          hash).

    Returns:

        Hexadecimal string of the perceptual hash.
    """
    # 1. Load image and convert to grayscale ('L')
    img = Image.open(image_path).convert("L")

    # 2. Resize to hash_size x hash_size using anti-aliasing
    img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)

    # 3. Extract pixel array
    pixels = np.array(img, dtype=np.float64)

    # 4. Explicitly compute the TRUE MEAN across all N x N pixels
    pixel_mean = np.mean(pixels)

    # 5. Compare each pixel to the calculated pixel_mean (NOT 128)
    # Result is a boolean grid where True = pixel >= mean, False = pixel < mean
    diff = pixels >= pixel_mean

    # 6. Pack boolean bits into bytes and format as a hex string
    packed_bytes = np.packbits(diff.flatten())
    return "".join(f"{byte:02x}" for byte in packed_bytes)


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Calculates bitwise differences between two hex hashes."""
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must be of equal length to compare.")

    val_a = int(hash_a, 16)
    val_b = int(hash_b, 16)

    # XOR identifies differing bits; bit_count() counts them (Python 3.10+)
    return (val_a ^ val_b).bit_count()