import numpy as np
from PIL import Image


def compute_ahash(image_path, hash_size=8):
    """
    Compute the classic average hash (aHash) perceptual hash of an image.

    Steps:
      1. Convert to grayscale.
      2. Resize to (hash_size, hash_size) using a box filter.
      3. Compute the mean of the pixel values.
      4. Set each bit to 1 if the pixel is >= mean, else 0.
      5. Pack the bit matrix into a big integer (row-major, MSB first).

    Returns an integer of hash_size*hash_size bits.
    """
    # 1. Grayscale
    img = Image.open(image_path).convert("L")
    # 2. Resize (BOX gives a simple average down-sample, matching the classic
    #    implementation which effectively averages blocks)
    img = img.resize((hash_size, hash_size), Image.BOX)
    pixels = np.asarray(img, dtype=np.float64)

    # 3. Mean
    avg = pixels.mean()

    # 4. Bit matrix (1 where pixel >= mean)
    bits = (pixels >= avg).astype(np.uint8)

    # 5. Pack row-major, MSB first
    hash_int = 0
    for bit in bits.flatten():
        hash_int = (hash_int << 1) | int(bit)
    return hash_int


def hamming_distance(hash_a, hash_b):
    """Number of differing bits between two integer hashes."""
    return bin(hash_a ^ hash_b).count("1")