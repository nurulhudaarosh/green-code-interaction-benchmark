import os
from pathlib import Path
import numpy as np
from PIL import Image


def preprocess_images(input_dir, output_dir, flat_value=None):
    """
    Grayscale and min-max normalize every image in input_dir to full 0-255
    range, save as PNG in output_dir, and return original min/max stats.

    Flat (uniform) images are handled specially: they are written as a
    constant image and flagged in the returned stats, so no division by
    zero occurs and callers can detect them.

    Args:
        input_dir: Directory of source images.
        output_dir: Directory for normalized PNGs.
        flat_value: Value to write for flat images. If None, the image's
            original (constant) value is preserved. Pass 0 to force black,
            or 128 for mid-gray.

    Returns:
        dict: {filename: {
            "original_min": int,
            "original_max": int,
            "flat": bool,          # True if the source had min == max
            "output_path": str,
        }}
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".gif"}
    stats = {}

    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in valid_exts:
            continue

        with Image.open(path) as img:
            gray = img.convert("L")
            arr = np.asarray(gray, dtype=np.float32)

        # Use integer-typed min/max so equality is exact and stable.
        orig_min = int(arr.min())
        orig_max = int(arr.max())
        is_flat = orig_max == orig_min

        if is_flat:
            # Preserve the constant value (or use caller override).
            fill = orig_min if flat_value is None else int(flat_value)
            fill = max(0, min(255, fill))
            norm = np.full(arr.shape, fill, dtype=np.uint8)
        else:
            scaled = (arr - orig_min) / (orig_max - orig_min) * 255.0
            norm = np.clip(np.round(scaled), 0, 255).astype(np.uint8)

        out_path = output_dir / f"{path.stem}.png"
        Image.fromarray(norm, mode="L").save(out_path, format="PNG")

        stats[path.name] = {
            "original_min": orig_min,
            "original_max": orig_max,
            "flat": is_flat,
            "output_path": str(out_path),
        }

    return stats