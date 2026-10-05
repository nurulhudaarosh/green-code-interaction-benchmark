import os
from PIL import Image
import numpy as np


def compute_statistics(input_dir):
    """
    Compute per-image grayscale statistics.

    Returns:
        dict: {
            filename: {
                "histogram": list of 256 integer counts,
                "mean": float,
                "std": float
            }
        }
    """
    results = {}

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

    for filename in sorted(os.listdir(input_dir)):
        filepath = os.path.join(input_dir, filename)

        # Skip directories and unsupported files
        if not os.path.isfile(filepath):
            continue

        if os.path.splitext(filename)[1].lower() not in valid_extensions:
            continue

        try:
            # Convert image to grayscale
            image = Image.open(filepath).convert("L")
            pixels = np.asarray(image, dtype=np.uint8)

            # 256-bin grayscale histogram: bins 0..255
            histogram = np.bincount(
                pixels.ravel(),
                minlength=256
            )[:256]

            # Pixel intensity statistics
            mean = float(np.mean(pixels))
            std = float(np.std(pixels))

            results[filename] = {
                "histogram": histogram.tolist(),
                "mean": mean,
                "std": std
            }

        except (OSError, ValueError):
            # Skip files that cannot be opened as images
            continue

    return results