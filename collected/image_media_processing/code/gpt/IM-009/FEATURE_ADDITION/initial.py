import os
import numpy as np
from PIL import Image


def compute_statistics(input_dir):
    """
    Compute per-image grayscale histogram, mean, and population
    standard deviation.

    Returns:
        dict: {
            filename: {
                "histogram": [256 integer counts],
                "mean": float,
                "std": float
            }
        }
    """
    results = {}

    for filename in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, filename)

        if not os.path.isfile(path):
            continue

        try:
            with Image.open(path) as img:
                # Convert image to grayscale
                gray = np.array(img.convert("L"))

                # 256-bin histogram for intensities 0-255
                histogram = np.bincount(
                    gray.ravel(), minlength=256
                ).tolist()

                # Mean pixel intensity
                mean = float(np.mean(gray))

                # Population standard deviation (ddof=0)
                std = float(np.std(gray, ddof=0))

                results[filename] = {
                    "histogram": histogram,
                    "mean": mean,
                    "std": std
                }

        except (OSError, ValueError):
            # Skip files that cannot be opened as images
            continue

    return results