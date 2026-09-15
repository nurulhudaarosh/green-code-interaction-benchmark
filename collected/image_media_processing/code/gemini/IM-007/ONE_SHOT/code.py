from PIL import Image


def compute_ahash(image_path: str, hash_size: int = 8) -> str:
    """Computes the Average Hash (aHash) for an image.

    Args:
        image_path: Path to the image file.
        hash_size: Width and height of the resized image (default is 8 for a 64-bit hash).

    Returns:
        A hexadecimal string representing the perceptual hash.
    """
    # 1. Open image and convert to grayscale ('L')
    with Image.open(image_path) as img:
        img = img.convert("L")
        # 2. Resize to hash_size x hash_size using anti-aliasing (Resampling.LANCZOS)
        img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())

    # 3. Calculate average pixel value
    avg_val = sum(pixels) / len(pixels)

    # 4. Generate binary array (1 if pixel >= average, else 0)
    bits = [1 if pixel >= avg_val else 0 for pixel in pixels]

    # 5. Convert binary list into a hex string
    binary_str = "".join(str(b) for b in bits)
    # Convert integer to hex, padding to expected hex string length
    hex_len = (hash_size * hash_size) // 4
    return f"{int(binary_str, 2):0{hex_len}x}"


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Calculates the Hamming distance between two hex hashes.

    Args:
        hash_a: Hexadecimal hash string.
        hash_b: Hexadecimal hash string.

    Returns:
        The number of differing bits between the two hashes.
    """
    # Convert hex strings to integers
    val_a = int(hash_a, 16)
    val_b = int(hash_b, 16)

    # XOR identifies differing bits, bit_count() counts how many 1s remain
    return (val_a ^ val_b).bit_count()


# Example Usage
if __name__ == "__main__":
    hash1 = compute_ahash("image1.jpg")
    hash2 = compute_ahash("image2.jpg")

    distance = hamming_distance(hash1, hash2)

    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hamming Distance: {distance}")