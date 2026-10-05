import os
from PIL import Image
import numpy as np


def compute_statistics(input_dir):
    """
    Compute per-image grayscale histogram, mean, and population
    standard deviation.

    Returns:
        dict: {
            filename: {
                "histogram": [256 bin counts],
                "mean": float,
                "std": float
            }
        }
    """
    results = {}

    for filename in sorted(os.listdir(input_dir)):
        filepath = os.path.join(input_dir, filename)

        if not os.path.isfile(filepath):
            continue

        try:
            with Image.open(filepath) as img:
                # Convert image to grayscale
                gray = np.asarray(img.convert("L"), dtype=np.uint8)

                # 256-bin histogram for intensity values 0-255
                histogram = np.bincount(
                    gray.ravel(),
                    minlength=256
                ).tolist()

                # Pixel intensity statistics
                mean = float(np.mean(gray))
                std = float(np.std(gray, ddof=0))  # population std

                results[filename] = {
                    "histogram": histogram,
                    "mean": mean,
                    "std": std
                }

        except (OSError, ValueError):
            # Skip files that are not valid/readable images
            continue

    return results