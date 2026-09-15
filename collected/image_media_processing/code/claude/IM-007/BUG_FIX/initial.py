from PIL import Image
import numpy as np


def compute_ahash(image_path, hash_size=8):
    """
    Compute the average hash (aHash) of an image.

    Algorithm:
      1. Load the image and convert to grayscale.
      2. Resize to (hash_size x hash_size) pixels, discarding detail.
      3. Compute the mean pixel value.
      4. Build a bit for each pixel: 1 if pixel >= mean else 0.
      5. Pack the bits into a single integer (the hash).

    Args:
        image_path (str): Path to the image file.
        hash_size (int): Side length of the square the image is
            reduced to before hashing. The resulting hash has
            hash_size * hash_size bits (default 8 -> 64-bit hash).

    Returns:
        int: The average hash as an unsigned integer.
    """
    # 1. Load and convert to grayscale ("L" mode = 8-bit luminance)
    image = Image.open(image_path).convert("L")

    # 2. Resize to hash_size x hash_size using a high-quality filter
    image = image.resize((hash_size, hash_size), Image.LANCZOS)

    # 3. Get pixel values as a numpy array
    pixels = np.asarray(image, dtype=np.float64)

    # 4. Compute mean and build the bit difference matrix
    avg = pixels.mean()
    bits = pixels >= avg

    # 5. Pack bits (row-major order) into a single integer
    hash_value = 0
    for bit in bits.flatten():
        hash_value = (hash_value << 1) | int(bit)

    return hash_value


def hamming_distance(hash_a, hash_b):
    """
    Compute the Hamming distance between two hashes, i.e. the number
    of bit positions in which they differ. Lower distance means the
    images are more visually similar.

    Args:
        hash_a (int): First hash value.
        hash_b (int): Second hash value.

    Returns:
        int: Number of differing bits.
    """
    return bin(hash_a ^ hash_b).count("1")


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3:
        h1 = compute_ahash(sys.argv[1])
        h2 = compute_ahash(sys.argv[2])
        print(f"Hash 1: {h1:016x}")
        print(f"Hash 2: {h2:016x}")
        print(f"Hamming distance: {hamming_distance(h1, h2)}")
    else:
        print("Usage: python ahash.py <image1> <image2>")