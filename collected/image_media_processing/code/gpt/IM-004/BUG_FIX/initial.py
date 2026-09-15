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
                # Convert to grayscale
                gray = img.convert("L")
                arr = np.asarray(gray, dtype=np.float32)

                original_min = float(arr.min())
                original_max = float(arr.max())

                stats[path.name] = {
                    "min": original_min,
                    "max": original_max
                }

                # Min-max normalization to 0-255
                if original_max > original_min:
                    normalized = (
                        (arr - original_min)
                        / (original_max - original_min)
                        * 255
                    )
                else:
                    # Constant image: avoid division by zero
                    normalized = np.zeros_like(arr)

                normalized = np.round(normalized).astype(np.uint8)

                # Save as PNG
                output_path = output_dir / f"{path.stem}.png"
                Image.fromarray(normalized, mode="L").save(output_path)

        except (OSError, ValueError):
            # Skip files that are not valid images
            continue

    return stats