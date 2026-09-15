from PIL import Image
import numpy as np

def compute_ahash(image_path, hash_size=8):
    """
    Computes the Average Hash (aHash) for a given image using the dynamic pixel mean.
    """
    # 1. Open image and convert to grayscale ('L')
    img = Image.open(image_path).convert('L')
    
    # 2. Resize to hash_size x hash_size
    img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    
    # 3. Convert image pixels to NumPy array
    pixels = np.array(img, dtype=np.float32)
    
    # 4. Compute the actual mean of the resized pixels (not 128)
    pixel_mean = pixels.mean()
    
    # 5. Compare each pixel value against the computed mean
    binary_matrix = pixels >= pixel_mean
    
    # 6. Flatten matrix into a binary string
    return ''.join('1' if bit else '0' for bit in binary_matrix.flatten())


def hamming_distance(hash_a, hash_b):
    """
    Calculates the Hamming distance between two binary hash strings.
    """
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must be of equal length to compare.")
        
    return sum(c1 != c2 for c1, c2 in zip(hash_a, hash_b))