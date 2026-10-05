import os
import numpy as np
from PIL import Image


def compute_statistics(input_dir):
    """
    Compute per-image 256-bin grayscale histogram, mean,
    median, and population standard deviation.

    Returns:
        dict: {
            filename: {
                "histogram": [256 integer counts],
                "mean": float,
                "median": float,
                "std": float
            }
        }
    """
    results = {}

    for filename in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, filename)

        # Skip directories and non-file entries
        if not os.path.isfile(path):
            continue

        try:
            with Image.open(path) as img:
                # Convert image to grayscale (0-255)
                gray = np.array(img.convert("L"))

                # 256-bin histogram
                histogram = np.bincount(
                    gray.ravel(),
                    minlength=256
                ).tolist()

                total_pixels = sum(histogram)

                # Mean pixel intensity
                mean = float(np.mean(gray))

                # Population standard deviation (divide by N)
                std = float(np.std(gray, ddof=0))

                # Median computed from the histogram
                if total_pixels == 0:
                    median = 0.0
                else:
                    # Positions of the two middle pixels
                    mid1 = (total_pixels - 1) // 2
                    mid2 = total_pixels // 2

                    cumulative = 0
                    value1 = None
                    value2 = None

                    for intensity, count in enumerate(histogram):
                        cumulative += count

                        if value1 is None and cumulative > mid1:
                            value1 = intensity

                        if cumulative > mid2:
                            value2 = intensity
                            break

                    median = (value1 + value2) / 2.0

                results[filename] = {
                    "histogram": histogram,
                    "mean": mean,
                    "median": median,
                    "std": std
                }

        except (OSError, ValueError):
            # Skip files that cannot be opened as images
            continue

    return results