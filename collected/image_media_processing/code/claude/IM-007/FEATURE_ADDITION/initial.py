from PIL import Image

def compute_ahash(image_path, hash_size=8):
    """
    Compute the average hash (aHash) of an image.

    Steps:
      1. Convert to grayscale
      2. Resize to (hash_size x hash_size)
      3. Compute the mean pixel value
      4. Set each bit to 1 if the pixel is >= mean, else 0

    Returns an integer representing the hash bits.
    """
    image = Image.open(image_path).convert("L")  # grayscale
    image = image.resize((hash_size, hash_size), Image.LANCZOS)

    pixels = list(image.getdata())
    avg = sum(pixels) / len(pixels)

    bits = 0
    for pixel in pixels:
        bits <<= 1
        if pixel >= avg:
            bits |= 1

    return bits


def hamming_distance(hash_a, hash_b):
    """
    Compute the Hamming distance between two hashes (as integers).
    Lower distance = more similar images.
    """
    return bin(hash_a ^ hash_b).count("1")