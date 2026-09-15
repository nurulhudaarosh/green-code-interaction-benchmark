from PIL import Image

def compute_ahash(image_path, hash_size=8):
    """
    Compute the average hash (aHash) of an image.

    Steps:
    1. Open image, convert to grayscale.
    2. Resize to (hash_size x hash_size) pixels.
    3. Compute the true mean of the resized pixel values.
    4. Build a bit for each pixel: 1 if pixel >= mean else 0.
    5. Pack bits into an integer.

    Returns:
        int: an integer with hash_size*hash_size bits representing the hash.
    """
    img = Image.open(image_path).convert("L")  # grayscale
    img = img.resize((hash_size, hash_size), Image.LANCZOS)

    pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)  # true mean of the resized pixels

    bits = 0
    for pixel in pixels:
        bits <<= 1
        if pixel >= avg:
            bits |= 1

    return bits


def hamming_distance(hash_a, hash_b):
    """
    Compute the Hamming distance between two integer hashes,
    i.e. the number of differing bits.
    """
    return bin(hash_a ^ hash_b).count("1")


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        h1 = compute_ahash(sys.argv[1])
        h2 = compute_ahash(sys.argv[2])
        print(f"Hash 1: {h1:016x}")
        print(f"Hash 2: {h2:016x}")
        print(f"Hamming distance: {hamming_distance(h1, h2)}")