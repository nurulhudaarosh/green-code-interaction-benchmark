import numpy as np
from PIL import Image


def compute_ahash(image_path: str, hash_size: int = 8) -> str:
    """Computes the average hash (aHash) for an image.

    Args:
        image_path: Path to the input image file.
        hash_size: Width and height of the resized image (default 8 for 64-bit
          hash).

    Returns:
        Hexadecimal string representation of the hash.
    """
    # 1. Open image, convert to grayscale, and resize with antialiasing
    img = Image.open(image_path).convert("L")
    img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)

    # 2. Convert pixel data to numpy array
    pixels = np.asarray(img, dtype=np.float32)

    # 3. Calculate mean pixel value
    avg_pixel = pixels.mean()

    # 4. Create boolean array (1 where pixel >= mean, 0 otherwise)
    diff = pixels >= avg_pixel

    # 5. Convert bit array into a hexadecimal string
    # Flatten the 2D boolean array into a 1D sequence of bits
    bits = diff.flatten()

    # Pack bits into uint8 bytes and convert to hex
    packed = np.packbits(bits)
    hash_hex = "".join(f"{byte:02x}" for byte in packed)

    return hash_hex


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Calculates the Hamming distance between two hex-encoded hashes.

    Args:
        hash_a: Hexadecimal hash string.
        hash_b: Hexadecimal hash string.

    Returns:
        The number of differing bits between the two hashes.
    """
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must be of equal length to compare.")

    # Convert hex strings back to byte arrays
    bytes_a = bytes.fromhex(hash_a)
    bytes_b = bytes.fromhex(hash_b)

    # XOR bytes to find bit differences and sum the set bits (1s)
    distance = 0
    for byte_a, byte_b in zip(bytes_a, bytes_b):
        xor_result = byte_a ^ byte_b
        distance += bin(xor_result).count("1")

    return distance