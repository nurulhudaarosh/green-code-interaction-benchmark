from PIL import Image

def compute_ahash(image_path, hash_size=8):
    """
    Compute the average hash (aHash) of an image.

    Steps:
      1. Load image and convert to grayscale.
      2. Resize to (hash_size x hash_size) pixels.
      3. Compute the mean pixel value.
      4. Build a bit for each pixel: 1 if pixel >= mean, else 0.
      5. Pack bits into a single integer.

    Returns:
        int: an integer whose lowest (hash_size*hash_size) bits encode the hash.
    """
    with Image.open(image_path) as img:
        # Grayscale + shrink to hash_size x hash_size
        img = img.convert("L").resize(
            (hash_size, hash_size), Image.Resampling.LANCZOS
        )
        pixels = list(img.getdata())

    avg = sum(pixels) / len(pixels)

    # Build the hash: bit i is 1 if pixels[i] >= avg
    bits = 0
    for pixel in pixels:
        bits <<= 1
        if pixel >= avg:
            bits |= 1

    return bits


def hamming_distance(hash_a, hash_b):
    """
    Compute the Hamming distance between two hashes.

    Works on integer hashes (as produced by compute_ahash) or equal-length
    strings of bits/hex — integers are converted directly, strings are
    parsed as binary.

    Returns:
        int: number of differing bits (0 = identical, higher = more different).
    """
    if isinstance(hash_a, str):
        hash_a = int(hash_a, 2)
    if isinstance(hash_b, str):
        hash_b = int(hash_b, 2)

    xor_result = hash_a ^ hash_b
    return bin(xor_result).count("1")