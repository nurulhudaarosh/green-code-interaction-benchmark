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
                "std": population standard deviation
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

            # 256-bin histogram for pixel values 0-255
            histogram = np.bincount(gray.ravel(), minlength=256)

            # Mean and population standard deviation
            mean = float(np.mean(gray))
            std = float(np.std(gray, ddof=0))

            results[filename] = {
                "histogram": histogram.tolist(),
                "mean": mean,
                "std": std
            }

        except (OSError, ValueError):
            # Skip files that are not valid/readable images
            continue

    return results