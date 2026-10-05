import os
import numpy as np
from PIL import Image
from pathlib import Path

def compute_statistics(input_dir):
    """
    Compute per-image 256-bin grayscale histograms plus mean and std of pixel intensity.
    
    Args:
        input_dir (str): Path to directory containing image files.
        
    Returns:
        dict: Mapping from relative file path to a dict with keys:
              - 'histogram': np.ndarray of shape (256,), counts (int64)
              - 'mean': float, mean pixel intensity
              - 'std': float, standard deviation of pixel intensity
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.gif', '.webp'}
    results = {}
    input_path = Path(input_dir)
    
    if not input_path.is_dir():
        raise NotADirectoryError(f"'{input_dir}' is not a valid directory")
    
    for file_path in sorted(input_path.rglob('*')):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in image_extensions:
            continue
        
        try:
            # Convert to 8-bit grayscale
            with Image.open(file_path) as img:
                gray = img.convert('L')
                pixels = np.asarray(gray, dtype=np.uint8)
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            continue
        
        # 256-bin histogram of grayscale intensities
        histogram = np.bincount(pixels.ravel(), minlength=256).astype(np.int64)
        
        # Mean and standard deviation of pixel intensity
        mean = float(pixels.mean())
        std = float(pixels.std())
        
        rel_path = str(file_path.relative_to(input_path))
        results[rel_path] = {
            'histogram': histogram,
            'mean': mean,
            'std': std,
        }
    
    return results


# Example usage
if __name__ == "__main__":
    stats = compute_statistics("./images")
    for name, s in stats.items():
        print(f"{name}: mean={s['mean']:.2f}, std={s['std']:.2f}, "
              f"hist_sum={s['histogram'].sum()}")