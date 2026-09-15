from PIL import Image

def compute_ahash(image_path, hash_size=8):
    """
    Compute the classic average-hash (aHash) perceptual hash of an image.
    
    Algorithm:
      1. Convert the image to grayscale.
      2. Resize to (hash_size, hash_size) using a high-quality downsampler.
      3. Compute the mean pixel value.
      4. Set each bit to 1 if the pixel is >= mean, else 0.
    
    Returns an integer whose low hash_size*hash_size bits encode the hash,
    with the top-left pixel as the most significant bit.
    """
    with Image.open(image_path) as img:
        img = img.convert("L").resize(
            (hash_size, hash_size), Image.Resampling.LANCZOS
        )
        pixels = list(img.getdata())

    avg = sum(pixels) / len(pixels)

    bits = 0
    for px in pixels:
        bits = (bits << 1) | (1 if px >= avg else 0)
    return bits


def hamming_distance(hash_a, hash_b):
    """
    Return the number of differing bits between two integer hashes
    (the Hamming distance).
    """
    return bin(hash_a ^ hash_b).count("1")