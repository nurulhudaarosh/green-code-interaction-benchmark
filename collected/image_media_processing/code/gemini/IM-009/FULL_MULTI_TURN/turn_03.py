from pathlib import Path
import cv2
import numpy as np


def compute_statistics(input_dir):
    """Computes per-image 256-bin grayscale histograms, mean, population standard deviation,
    and median pixel intensity.

    Args:
        input_dir (str or Path): Path to directory containing images.

    Returns:
        dict: Mapping of image filename to a dict containing:
            - 'histogram': np.ndarray of shape (256,) with bin counts
            - 'mean': float, average pixel intensity
            - 'std': float, population standard deviation (ddof=0)
            - 'median': int, median pixel intensity computed from the histogram
    """
    valid_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
    }
    input_path = Path(input_dir)
    results = {}

    for file_path in input_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            # Read image in grayscale mode (0-255 uint8)
            img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)

            if img is None:
                continue

            # 256-bin histogram over pixel values [0, 256]
            hist = cv2.calcHist([img], [0], None, [256], [0, 256]).flatten()

            # Population Mean and Standard Deviation (ddof=0 divides by N)
            mean_val = float(np.mean(img))
            std_val = float(np.std(img, ddof=0))

            # Median pixel intensity computed from histogram cumulative sum
            cdf = np.cumsum(hist)
            total_pixels = img.size
            median_val = int(np.searchsorted(cdf, total_pixels / 2.0))

            results[file_path.name] = {
                "histogram": hist.astype(np.int64),
                "mean": mean_val,
                "std": std_val,
                "median": median_val,
            }

    return results