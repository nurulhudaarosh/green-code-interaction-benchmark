import os
from PIL import Image
import numpy as np


def compute_statistics(input_dir):
    """
    Compute per-image grayscale statistics.

    Returns:
        dict: {
            filename: {
                "histogram": 256-bin grayscale histogram,
                "mean": mean pixel intensity,
                "std": population standard deviation,
                "median": median pixel intensity
            }
        }
    """
    results = {}

    for filename in sorted(os.listdir(input_dir)):
        filepath = os.path.join(input_dir, filename)

        # Skip directories and non-files
        if not os.path.isfile(filepath):
            continue

        try:
            with Image.open(filepath) as img:
                # Convert image to grayscale
                gray = np.array(img.convert("L"), dtype=np.uint8)

            # Flatten pixel values
            pixels = gray.ravel()

            # 256-bin histogram for pixel values 0-255
            histogram = np.bincount(pixels, minlength=256)

            # Mean pixel intensity
            mean = float(np.mean(pixels))

            # Population standard deviation (divide by N)
            std = float(np.std(pixels, ddof=0))

            # Compute median from the histogram
            total_pixels = int(histogram.sum())

            cumulative = np.cumsum(histogram)

            if total_pixels % 2 == 1:
                # Odd number of pixels
                middle = total_pixels // 2 + 1
                median = float(np.searchsorted(cumulative, middle))

            else:
                # Even number of pixels
                middle1 = total_pixels // 2
                middle2 = middle1 + 1

                median1 = np.searchsorted(cumulative, middle1)
                median2 = np.searchsorted(cumulative, middle2)

                median = float((median1 + median2) / 2.0)

            results[filename] = {
                "histogram": histogram.tolist(),
                "mean": mean,
                "std": std,
                "median": median
            }

        except (OSError, ValueError):
            # Skip files that are not valid/readable images
            continue

    return results