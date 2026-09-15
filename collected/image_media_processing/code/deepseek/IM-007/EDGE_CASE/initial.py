import numpy as np
from PIL import Image


def compute_ahash(image_path, hash_size=8):
    """
    Compute the classic average hash (aHash) of an image.

    Steps:
      1. Load image and convert to grayscale.
      2. Resize to (hash_size x hash_size) using area/lanczos resampling.
      3. Compute the mean pixel value.
      4. Build a bit string: 1 if pixel > mean, else 0.
      5. Pack bits into a NumPy uint8 array of length hash_size*hash_size // 8.

    Args:
        image_path: Path to the image file.
        hash_size: Side length of the square hash (default 8 -> 64-bit hash).

    Returns:
        A 1-D NumPy uint8 array representing the packed bits.
    """
    if hash_size <= 0:
        raise ValueError("hash_size must be a positive integer")
    if (hash_size * hash_size) % 8 != 0:
        raise ValueError("hash_size * hash_size must be a multiple of 8")

    # 1) Load and convert to grayscale
    with Image.open(image_path) as img:
        img = img.convert("L")
        # 2) Resize to hash_size x hash_size
        img = img.resize((hash_size, hash_size), Image.LANCZOS)

        # 3) Get pixel data as a 2-D array
        pixels = np.asarray(img, dtype=np.float32)

    # 4) Compare against the mean
    mean = pixels.mean()
    bits = (pixels > mean).astype(np.uint8).flatten()

    # 5) Pack bits into bytes (MSB first within each byte)
    packed = np.packbits(bits)
    return packed


def hamming_distance(hash_a, hash_b):
    """
    Compute the Hamming distance between two packed bit hashes.

    Args:
        hash_a: 1-D NumPy uint8 array (or bytes) of packed bits.
        hash_b: 1-D NumPy uint8 array (or bytes) of packed bits.

    Returns:
        Integer Hamming distance (number of differing bits).
    """
    a = np.asarray(hash_a, dtype=np.uint8)
    b = np.asarray(hash_b, dtype=np.uint8)

    if a.shape != b.shape:
        raise ValueError(
            f"Hash shapes must match: {a.shape} vs {b.shape}"
        )

    # XOR the bytes, then count the set bits
    xor = np.bitwise_xor(a, b)
    return int(np.unpackbits(xor).sum())


if __name__ == "__main__":
    # Simple demo
    h1 = compute_ahash("image1.jpg")
    h2 = compute_ahash("image2.jpg")
    print("Hash 1:", h1)
    print("Hash 2:", h2)
    print("Hamming distance:", hamming_distance(h1, h2))