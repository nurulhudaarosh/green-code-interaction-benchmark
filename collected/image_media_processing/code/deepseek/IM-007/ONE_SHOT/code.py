from PIL import Image
import numpy as np

def compute_ahash(image_path, hash_size=8):
    """
    Compute the average hash (aHash) of an image.
    
    Algorithm:
    1. Convert image to grayscale
    2. Resize to (hash_size x hash_size) using area averaging
    3. Compute the mean pixel value
    4. Set each bit to 1 if pixel > mean, else 0
    
    Args:
        image_path: Path to the image file
        hash_size: Size of the hash (default 8 -> 64-bit hash)
    
    Returns:
        A numpy array of bits (dtype=uint8), flattened, length hash_size*hash_size
    """
    # Load and convert to grayscale
    with Image.open(image_path) as img:
        img = img.convert("L")
        # Resize using LANCZOS for good downsampling quality
        img = img.resize((hash_size, hash_size), Image.LANCZOS)
        pixels = np.asarray(img, dtype=np.float64)
    
    # Compute mean and threshold
    avg = pixels.mean()
    bits = (pixels > avg).astype(np.uint8)
    
    return bits.flatten()


def hamming_distance(hash_a, hash_b):
    """
    Compute the Hamming distance between two binary hashes.
    
    Args:
        hash_a, hash_b: 1-D arrays of bits (0/1), same length
    
    Returns:
        Integer count of differing bit positions
    """
    a = np.asarray(hash_a, dtype=np.uint8)
    b = np.asarray(hash_b, dtype=np.uint8)
    if a.shape != b.shape:
        raise ValueError(f"Hash shapes differ: {a.shape} vs {b.shape}")
    return int(np.count_nonzero(a != b))