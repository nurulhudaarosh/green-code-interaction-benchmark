import os
import cv2
import numpy as np

def compute_statistics(input_dir: str) -> dict:
    """
    Computes 256-bin grayscale histograms, mean, and std deviation
    for all images in a given directory.

    Args:
        input_dir (str): Path to the folder containing image files.

    Returns:
        dict: A dictionary mapping filenames to their computed statistics:
              {
                  'filename.jpg': {
                      'histogram': np.ndarray, # Shape (256, 1), float32
                      'mean': float,
                      'std': float
                  },
                  ...
              }
    """
    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')
    stats = {}

    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Directory '{input_dir}' does not exist.")

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        filepath = os.path.join(input_dir, filename)
        
        # Load image directly in grayscale
        img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue

        # Compute 256-bin histogram (range 0 to 256)
        hist = cv2.calcHist([img], [0], None, [256], [0, 256])

        # Compute pixel intensity mean and standard deviation
        mean_val, std_val = cv2.meanStdDev(img)

        stats[filename] = {
            'histogram': hist,
            'mean': float(mean_val[0][0]),
            'std': float(std_val[0][0])
        }

    return stats