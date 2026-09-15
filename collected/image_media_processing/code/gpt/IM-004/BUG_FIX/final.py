from pathlib import Path
from PIL import Image
import numpy as np


def preprocess_images(input_dir, output_dir):
    """
    Grayscale and min-max normalize every image to the full 0-255 range.

    Returns:
        dict: {filename: {"min": original_min, "max": original_max}}
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {}

    for path in input_dir.iterdir():
        if not path.is_file():
            continue

        try:
            with Image.open(path) as img:
                gray = img.convert("L")
                arr = np.asarray(gray, dtype=np.float32)

                lo = float(arr.min())
                hi = float(arr.max())

                stats[path.name] = {
                    "min": lo,
                    "max": hi
                }

                # Handle uniformly-colored (flat) images
                if hi == lo:
                    normalized = np.zeros_like(arr, dtype=np.uint8)
                else:
                    normalized = (
                        (arr - lo) / (hi - lo) * 255
                    ).round().astype(np.uint8)

                output_path = output_dir / f"{path.stem}.png"
                Image.fromarray(normalized, mode="L").save(output_path)

        except (OSError, ValueError):
            # Skip files that are not valid images
            continue

    return stats