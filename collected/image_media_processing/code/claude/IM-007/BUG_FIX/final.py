from PIL import Image
import numpy as np


def compute_ahash(image_path, hash_size=8):
    """
    Compute the average hash (aHash) of an image.

    The threshold is the TRUE MEAN of the resized grayscale pixels,
    recomputed per image -- NOT a fixed constant like 128. Using a
    hardcoded threshold breaks the whole point of aHash: it would make
    the hash sensitive to brightness shifts (e.g. a uniformly brightened
    or darkened version of the same image would hash very differently),
    instead of tolerant of them.
    """
    image = Image.open(image_path).convert("L")
    image = image.resize((hash_size, hash_size), Image.LANCZOS)

    pixels = np.asarray(image, dtype=np.float64)

    # Correct: threshold = mean of THIS image's resized pixels
    avg = pixels.mean()

    # WRONG (the bug): bits = pixels >= 128
    bits = pixels >= avg

    hash_value = 0
    for bit in bits.flatten():
        hash_value = (hash_value << 1) | int(bit)

    return hash_value


def hamming_distance(hash_a, hash_b):
    return bin(hash_a ^ hash_b).count("1")