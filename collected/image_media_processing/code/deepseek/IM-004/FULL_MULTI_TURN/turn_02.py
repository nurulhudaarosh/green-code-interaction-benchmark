import os
import json
import numpy as np
from PIL import Image
from pathlib import Path


def preprocess_images(input_dir, output_dir, flat_value=0):
    """
    Grayscale and min-max normalize every image in input_dir to full 0-255 range.
    Saves normalized images as PNG in output_dir.

    Args:
        input_dir (str): Directory containing source images.
        output_dir (str): Directory to save normalized PNGs.
        flat_value (int): Pixel value to assign to uniformly-colored (flat)
            images where max == min. Default 0 (black). Use 127 for mid-gray.

    Returns:
        dict: Mapping of relative output filename -> {
            'source': original filename,
            'original_min': int,
            'original_max': int,
            'flat': bool,  # True if the image had no dynamic range
        }
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not 0 <= flat_value <= 255:
        raise ValueError("flat_value must be in [0, 255]")

    valid_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.webp', '.gif'}
    stats = {}

    for src_path in sorted(input_dir.rglob('*')):
        if not src_path.is_file() or src_path.suffix.lower() not in valid_exts:
            continue

        # Load and convert to grayscale ('L' mode yields uint8)
        with Image.open(src_path) as img:
            gray = img.convert('L')
            arr = np.asarray(gray, dtype=np.uint8)

        orig_min = int(arr.min())
        orig_max = int(arr.max())
        is_flat = (orig_max == orig_min)

        if is_flat:
            # Uniform image: no dynamic range to stretch.
            # Produce a constant image at flat_value instead of dividing by zero.
            norm = np.full(arr.shape, flat_value, dtype=np.uint8)
        else:
            # Min-max normalize to full 0-255 range.
            span = float(orig_max - orig_min)  # nonzero here
            norm = (arr.astype(np.float32) - orig_min) / span
            norm = np.clip(norm * 255.0, 0, 255).astype(np.uint8)

        # Preserve subdirectory structure, force .png extension
        rel = src_path.relative_to(input_dir)
        out_name = rel.with_suffix('.png')
        out_path = output_dir / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        Image.fromarray(norm, mode='L').save(out_path, format='PNG')

        stats[str(out_name)] = {
            'source': str(rel),
            'original_min': orig_min,
            'original_max': orig_max,
            'flat': is_flat,
        }

    return stats


if __name__ == '__main__':
    stats = preprocess_images('input_images', 'output_images')
    print(json.dumps(stats, indent=2))

    with open(Path('output_images') / 'stats.json', 'w') as f:
        json.dump(stats, f, indent=2)