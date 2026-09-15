from PIL import Image


def compute_ahash(image_path, hash_size=8):
    """
    Compute the average hash (aHash) of an image.

    Classic algorithm:
      1. Load the image and convert to grayscale.
      2. Resize to (hash_size x hash_size) pixels.
      3. Compute the mean pixel value.
      4. Build a bit for each pixel: 1 if pixel >= mean, else 0.
      5. Pack the bits into an integer (the hash).

    Args:
        image_path (str): Path to the image file.
        hash_size (int): Side length of the square the image is
            downsampled to. The resulting hash has hash_size**2 bits.
            Default is 8 (64-bit hash).

    Returns:
        int: An integer whose lowest hash_size*hash_size bits encode
            the hash (bit i corresponds to pixel i in row-major order,
            with bit (hash_size*hash_size - 1) being the first pixel).
    """
    if hash_size <= 0:
        raise ValueError("hash_size must be a positive integer")

    with Image.open(image_path) as img:
        # Convert to grayscale ('L' mode) and shrink to hash_size x hash_size.
        # Image.LANCZOS gives good quality; ANTIALIAS is deprecated in newer Pillow.
        resample = getattr(Image, "LANCZOS", None) or Image.ANTIALIAS
        small = img.convert("L").resize((hash_size, hash_size), resample)

        pixels = list(small.getdata())

    avg = sum(pixels) / len(pixels)

    # Build the hash: 1 bit per pixel, 1 if pixel value >= average.
    bits = 0
    for pixel in pixels:
        bits <<= 1
        if pixel >= avg:
            bits |= 1

    return bits


def hamming_distance(hash_a, hash_b):
    """
    Compute the Hamming distance between two integer hashes,
    i.e. the number of bit positions at which they differ.

    Args:
        hash_a (int): First hash.
        hash_b (int): Second hash.

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