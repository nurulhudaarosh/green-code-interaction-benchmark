import os
from pathlib import Path
from PIL import Image
import numpy as np

def preprocess_images(input_dir, output_dir):
    """
    Grayscale + min-max normalize every image in input_dir to full 0-255 range,
    save as PNG in output_dir, and return per-file original min/max stats.

    Uniformly-colored (flat) images, where min == max, are handled specially
    to avoid a ZeroDivisionError: they are output as a flat black image
    instead of attempting to divide by zero.

    Returns:
        dict: {filename: {"min": original_min, "max": original_max}}
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
    stats = {}

    for file_path in sorted(input_dir.iterdir()):
        if file_path.suffix.lower() not in valid_exts:
            continue

        try:
            img = Image.open(file_path).convert("L")  # grayscale
        except Exception as e:
            print(f"Skipping {file_path.name}: {e}")
            continue

        arr = np.array(img, dtype=np.float64)
        orig_min = float(arr.min())
        orig_max = float(arr.max())

        if orig_max > orig_min:
            norm = (arr - orig_min) / (orig_max - orig_min) * 255.0
        else:
            # Flat/uniform image: min == max, division would raise
            # ZeroDivisionError (or produce NaNs with numpy arrays).
            # Output a flat black image instead.
            norm = np.zeros_like(arr)

        norm = norm.clip(0, 255).astype(np.uint8)

        out_name = file_path.stem + ".png"
        out_path = output_dir / out_name
        Image.fromarray(norm, mode="L").save(out_path, format="PNG")

        stats[file_path.name] = {"min": orig_min, "max": orig_max}

    return stats


if __name__ == "__main__":
    result = preprocess_images("input_images", "output_images")
    for fname, s in result.items():
        print(f"{fname}: min={s['min']}, max={s['max']}")