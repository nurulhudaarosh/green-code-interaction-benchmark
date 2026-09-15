from PIL import Image
import numpy as np

def compute_ahash(image_path, hash_size=8):
    """
    Computes the Average Hash (aHash) for a given image.
    
    Parameters:
        image_path (str): Path to the image file.
        hash_size (int): Dimensions of the resized square image (default: 8 for 64-bit hash).
        
    Returns:
        str: Binary string representation of the perceptual hash.
    """
    # 1. Open the image and convert to grayscale
    img = Image.open(image_path).convert('L')
    
    # 2. Shrink image down using high-quality anti-aliasing (LANCZOS)
    img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    
    # 3. Convert image data to a numpy array
    pixels = np.array(img, dtype=np.float32)
    
    # 4. Calculate the average pixel value
    avg = pixels.mean()
    
    # 5. Compute the boolean array: 1 if pixel >= average, 0 otherwise
    diff = pixels >= avg
    
    # 6. Convert boolean matrix to a binary string
    hash_str = ''.join('1' if val else '0' for val in diff.flatten())
    
    return hash_str


def hamming_distance(hash_a, hash_b):
    """
    Calculates the Hamming distance between two hash strings of equal length.
    
    Parameters:
        hash_a (str): First binary hash string.
        hash_b (str): Second binary hash string.
        
    Returns:
        int: Number of positions where the two hashes differ.
    """
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must be of equal length to compare.")
        
    return sum(char1 != char2 for char1, char2 in zip(hash_a, hash_b))