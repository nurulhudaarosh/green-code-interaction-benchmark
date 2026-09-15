from pathlib import Path
import numpy as np
from PIL import Image


def preprocess_images(input_dir, output_dir):
    """
    Grayscale and min-max normalize every image in input_dir to the full 0-255 range,
    saving results as PNGs in output_dir.

    Args:
        input_dir (str | Path): Directory containing source images.
        output_dir (str | Path): Directory to write normalized PNGs to.

    Returns:
        dict: Mapping of {relative_output_filename: {
                  "original_min": int,
                  "original_max": int,
              }}
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {}

    # Common image extensions; adjust if you have other formats
    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

    for src_path in sorted(input_dir.rglob("*")):
        if not src_path.is_file() or src_path.suffix.lower() not in valid_exts:
            continue

        # Preserve subdirectory structure relative to input_dir
        rel_path = src_path.relative_to(input_dir)
        dst_path = output_dir / rel_path.with_suffix(".png")
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # Load and convert to grayscale ('L' mode = 8-bit luminance)
        with Image.open(src_path) as img:
            gray = img.convert("L")
            arr = np.asarray(gray, dtype=np.float32)

        orig_min = int(arr.min())
        orig_max = int(arr.max())

        # Min-max normalize to [0, 255]
        if orig_max > orig_min:
            normalized = (arr - orig_min) / (orig_max - orig_min) * 255.0
        else:
            # Constant image — avoid divide-by-zero; map to zeros
            normalized = np.zeros_like(arr)

        # Round and clip to be safe, then cast back to uint8
        normalized = np.clip(np.rint(normalized), 0, 255).astype(np.uint8)

        Image.fromarray(normalized, mode="L").save(dst_path, format="PNG")

        stats[str(dst_path.relative_to(output_dir))] = {
            "original_min": orig_min,
            "original_max": orig_max,
        }

    return stats