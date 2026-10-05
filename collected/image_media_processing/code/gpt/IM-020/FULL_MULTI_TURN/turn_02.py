from pathlib import Path
from PIL import Image
import numpy as np


def analyze_brightness(input_dir):
    """
    Analyze brightness statistics for every valid image.

    Returns a list of dictionaries containing:
        filename, r_mean, g_mean, b_mean,
        brightness, classification
    """
    input_dir = Path(input_dir)

    valid_extensions = {
        ".jpg", ".jpeg", ".png", ".bmp",
        ".tif", ".tiff", ".webp"
    }

    results = []

    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in valid_extensions:
            continue

        try:
            with Image.open(path) as img:
                # Per-channel means
                rgb = img.convert("RGB")
                rgb_array = np.asarray(rgb, dtype=np.float64)

                r_mean = float(rgb_array[:, :, 0].mean())
                g_mean = float(rgb_array[:, :, 1].mean())
                b_mean = float(rgb_array[:, :, 2].mean())

                # IMPORTANT:
                # Convert to true grayscale ("L") first.
                # PIL's L conversion applies perceptual luminance weighting.
                grayscale = img.convert("L")
                grayscale_array = np.asarray(grayscale, dtype=np.float64)

                brightness = float(grayscale_array.mean())

                # Classification based on grayscale brightness
                if brightness < 85:
                    classification = "dark"
                elif brightness >= 170:
                    classification = "bright"
                else:
                    classification = "normal"

                results.append({
                    "filename": path.name,
                    "r_mean": r_mean,
                    "g_mean": g_mean,
                    "b_mean": b_mean,
                    "brightness": brightness,
                    "classification": classification,
                })

        except (OSError, ValueError):
            # Ignore files that cannot be read as valid images
            continue

    return results