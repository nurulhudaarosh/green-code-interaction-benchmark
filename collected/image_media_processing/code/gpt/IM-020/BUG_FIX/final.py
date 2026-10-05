from pathlib import Path
from PIL import Image
import numpy as np


def analyze_brightness(input_dir):
    """
    Analyze per-channel means and perceptual grayscale brightness
    for every valid image in input_dir.

    Returns:
        dict: {
            filename: {
                "channel_means": {
                    "red": float,
                    "green": float,
                    "blue": float
                },
                "grayscale_brightness": float,
                "classification": "dark" | "normal" | "bright"
            }
        }
    """
    input_dir = Path(input_dir)

    if not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")

    results = {}
    valid_extensions = {
        ".jpg", ".jpeg", ".png", ".bmp",
        ".tif", ".tiff", ".webp"
    }

    for image_path in sorted(input_dir.iterdir()):
        if (
            not image_path.is_file()
            or image_path.suffix.lower() not in valid_extensions
        ):
            continue

        try:
            with Image.open(image_path) as img:
                # RGB image for per-channel statistics.
                rgb = img.convert("RGB")
                rgb_array = np.asarray(rgb, dtype=np.float32)

                channel_means = {
                    "red": float(rgb_array[:, :, 0].mean()),
                    "green": float(rgb_array[:, :, 1].mean()),
                    "blue": float(rgb_array[:, :, 2].mean()),
                }

                # IMPORTANT:
                # Use Pillow's true L-mode conversion, which applies
                # perceptual luminance weighting instead of equal
                # averaging of R, G, and B.
                grayscale = img.convert("L")
                grayscale_array = np.asarray(grayscale, dtype=np.float32)

                brightness = float(grayscale_array.mean())

                if brightness < 85:
                    classification = "dark"
                elif brightness < 170:
                    classification = "normal"
                else:
                    classification = "bright"

                results[image_path.name] = {
                    "channel_means": channel_means,
                    "grayscale_brightness": brightness,
                    "classification": classification,
                }

        except (OSError, ValueError):
            # Ignore files that cannot be opened as valid images.
            continue

    return results