import os
import cv2
import numpy as np

def compute_statistics(input_dir):
    """
    Computes per-image 256-bin grayscale histograms, mean, and standard deviation
    for all valid image files in a given directory.

    Args:
        input_dir (str): Path to the directory containing images.

    Returns:
        dict: A dictionary mapping image filenames to a dictionary containing:
            - 'histogram': np.ndarray of shape (256, 1) representing bin counts
            - 'mean': float, mean pixel intensity
            - 'std': float, standard deviation of pixel intensity
    """
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
    results = {}

    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Directory non-existent: {input_dir}")

    for filename in sorted(os.listdir(input_dir)):
        if filename.lower().endswith(valid_extensions):
            file_path = os.path.join(input_dir, filename)
            
            # Read image directly in grayscale (8-bit depth)
            img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            
            if img is None:
                continue
            
            # Compute 256-bin histogram (range 0 to 256)
            hist = cv2.calcHist([img], [0], None, [256], [0, 256])
            
            # Compute mean and standard deviation of pixel intensities
            mean, std = cv2.meanStdDev(img)
            
            results[filename] = {
                'histogram': hist,
                'mean': float(mean[0][0]),
                'std': float(std[0][0])
            }

    return results