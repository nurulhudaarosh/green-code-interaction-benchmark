from PIL import Image


def compute_ahash(image_path, hash_size=8):
    """
    Compute the average hash (aHash) of an image.

    Args:
        image_path (str): Path to the image file.
        hash_size (int): Width and height of the hash grid.

    Returns:
        str: Binary hash string of length hash_size * hash_size.
    """
    if hash_size <= 0:
        raise ValueError("hash_size must be greater than 0")

    with Image.open(image_path) as img:
        # Convert image to grayscale and resize it.
        img = img.convert("L").resize((hash_size, hash_size))

        # Get grayscale pixel values.
        pixels = list(img.getdata())

        # Calculate the mean pixel value.
        average = sum(pixels) / len(pixels)

        # Pixels equal to the mean are consistently treated as 1.
        return "".join(
            "1" if pixel >= average else "0"
            for pixel in pixels
        )


def hamming_distance(hash_a, hash_b):
    """
    Calculate the Hamming distance between two binary hashes.

    Args:
        hash_a (str): First binary hash.
        hash_b (str): Second binary hash.

    Returns:
        int: Number of differing bits.
    """
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must have the same length")

    return sum(
        bit_a != bit_b
        for bit_a, bit_b in zip(hash_a, hash_b)
    )