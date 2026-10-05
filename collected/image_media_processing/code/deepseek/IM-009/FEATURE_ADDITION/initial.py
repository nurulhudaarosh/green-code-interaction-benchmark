import os
import cv2
import numpy as np
from pathlib import Path

def compute_statistics(input_dir):
    """
    Compute per-image 256-bin grayscale histograms, mean, and standard deviation
    of pixel intensity for all images in a directory.
    
    Args:
        input_dir (str): Path to directory containing images.
    
    Returns:
        dict: Maps image filename -> {
            'histogram': np.ndarray of shape (256,),
            'mean': float,
            'std': float
        }
    """
    # Supported image extensions
    valid_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.webp'}
    
    results = {}
    input_path = Path(input_dir)
    
    if not input_path.is_dir():
        raise ValueError(f"'{input_dir}' is not a valid directory.")
    
    for file_path in sorted(input_path.iterdir()):
        if file_path.suffix.lower() not in valid_exts:
            continue
        
        # Read image in grayscale
        img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"Warning: could not read '{file_path.name}', skipping.")
            continue
        
        # Flatten pixel values
        pixels = img.ravel()
        
        # 256-bin histogram (counts of each intensity level 0-255)
        histogram = np.bincount(pixels, minlength=256).astype(np.int64)
        
        # Mean and standard deviation of pixel intensity
        mean = float(np.mean(pixels))
        std = float(np.std(pixels))
        
        results[file_path.name] = {
            'histogram': histogram,
            'mean': mean,
            'std': std
        }
    
    return results


if __name__ == '__main__':
    import sys
    stats = compute_statistics(sys.argv[1] if len(sys.argv) > 1 else '.')
    for name, s in stats.items():
        print(f"{name}: mean={s['mean']:.2f}, std={s['std']:.2f}, "
              f"hist_sum={s['histogram'].sum()}")