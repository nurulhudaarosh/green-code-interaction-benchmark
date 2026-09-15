from pathlib import Path
from PIL import Image
import numpy as np


def preprocess_images(input_dir, output_dir):
    """
    Grayscale and min-max normalize every image in input_dir to 0-255,
    save as PNG in output_dir, and return original min/max statistics.

    Returns:
        dict: {filename: {"min": original_min, "max": original_max}}
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {}

    for file_path in input_dir.iterdir():
        if not file_path.is_file():
            continue

        try:
            with Image.open(file_path) as img:
                # Convert to grayscale
                gray = img.convert("L")
                arr = np.array(gray, dtype=np.float32)

                # Store original min/max
                lo = float(arr.min())
                hi = float(arr.max())

                stats[file_path.name] = {
                    "min": lo,
                    "max": hi
                }

                # Min-max normalization
                if hi == lo:
                    # Flat image: avoid division by zero
                    normalized = np.zeros_like(arr, dtype=np.uint8)
                else:
                    normalized = ((arr - lo) / (hi - lo) * 255).astype(np.uint8)

                # Save as PNG
                output_path = output_dir / f"{file_path.stem}.png"
                Image.fromarray(normalized, mode="L").save(output_path)

        except (OSError, ValueError):
            # Skip files that are not valid/readable images
            continue

    return stats