import os
from pathlib import Path

import numpy as np
from PIL import Image


def preprocess_images(input_dir, output_dir):
    """
    Grayscale and min-max normalize every image in input_dir to the full 0-255 range,
    save as PNG in output_dir, and return per-file original min/max stats.

    Args:
        input_dir (str | Path): Directory containing input images.
        output_dir (str | Path): Directory to save processed PNGs.

    Returns:
        dict: Mapping of filename -> {"original_min": int, "original_max": int}
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
    stats = {}

    for img_path in sorted(input_dir.iterdir()):
        if not img_path.is_file() or img_path.suffix.lower() not in valid_exts:
            continue

        # Load and convert to grayscale ('L' mode = 8-bit grayscale)
        with Image.open(img_path) as img:
            gray = img.convert("L")

        arr = np.asarray(gray, dtype=np.float32)

        orig_min = int(arr.min())
        orig_max = int(arr.max())

        # Min-max normalize to 0-255
        if orig_max > orig_min:
            normalized = (arr - orig_min) / (orig_max - orig_min) * 255.0
        else:
            # Constant image: map everything to 0 (or could pick 255)
            normalized = np.zeros_like(arr)

        normalized = np.clip(normalized, 0, 255).astype(np.uint8)

        # Save as PNG (stem preserved, extension forced to .png)
        out_path = output_dir / (img_path.stem + ".png")
        Image.fromarray(normalized, mode="L").save(out_path, format="PNG")

        stats[img_path.name] = {
            "original_min": orig_min,
            "original_max": orig_max,
        }

    return stats


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python preprocess_images.py <input_dir> <output_dir>")
        sys.exit(1)

    result = preprocess_images(sys.argv[1], sys.argv[2])
    for name, s in result.items():
        print(f"{name}: min={s['original_min']}, max={s['original_max']}")