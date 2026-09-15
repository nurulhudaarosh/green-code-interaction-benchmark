import os
from pathlib import Path
from PIL import Image
import numpy as np

def preprocess_images(input_dir, output_dir, clip_percentile=None):
    """
    Grayscale + min-max normalize every image in input_dir to full 0-255 range,
    save as PNG in output_dir, and return per-file stats.

    Uniformly-colored (flat) images (min == max after any clipping) are handled
    specially to avoid a ZeroDivisionError: they are output as a flat black
    image instead of attempting to divide by zero.

    Args:
        input_dir (str or Path): directory of source images.
        output_dir (str or Path): directory to write normalized PNGs.
        clip_percentile (float | tuple[float, float] | None): if provided,
            clips pixel values to a percentile range before computing the
            min/max used for normalization, making the result robust to
            outlier pixels (e.g. hot pixels, sensor noise).
            - float p: symmetric clip at [p, 100 - p] (e.g. 1 -> clip below
              the 1st percentile and above the 99th percentile).
            - tuple (lo_pct, hi_pct): asymmetric clip range.
            - None (default): no clipping; uses true image min/max.

    Returns:
        dict: {
            filename: {
                "min": <original unclipped min>,
                "max": <original unclipped max>,
                "norm_min": <value mapped to 0, after any clipping>,
                "norm_max": <value mapped to 255, after any clipping>,
            }
        }
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
    stats = {}

    # Resolve percentile bounds once
    if clip_percentile is not None:
        if isinstance(clip_percentile, (tuple, list)):
            lo_pct, hi_pct = clip_percentile
        else:
            lo_pct, hi_pct = clip_percentile, 100 - clip_percentile

        if not (0 <= lo_pct < hi_pct <= 100):
            raise ValueError(
                f"Invalid clip_percentile bounds: ({lo_pct}, {hi_pct}). "
                "Require 0 <= lo_pct < hi_pct <= 100."
            )

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

        if clip_percentile is not None:
            norm_min = float(np.percentile(arr, lo_pct))
            norm_max = float(np.percentile(arr, hi_pct))
            arr = arr.clip(norm_min, norm_max)
        else:
            norm_min = orig_min
            norm_max = orig_max

        if norm_max > norm_min:
            norm = (arr - norm_min) / (norm_max - norm_min) * 255.0
        else:
            # Flat/uniform (post-clip) image: min == max, division would
            # raise ZeroDivisionError (or produce NaNs with numpy arrays).
            # Output a flat black image instead.
            norm = np.zeros_like(arr)

        norm = norm.clip(0, 255).astype(np.uint8)

        out_name = file_path.stem + ".png"
        out_path = output_dir / out_name
        Image.fromarray(norm, mode="L").save(out_path, format="PNG")

        stats[file_path.name] = {
            "min": orig_min,
            "max": orig_max,
            "norm_min": norm_min,
            "norm_max": norm_max,
        }

    return stats


if __name__ == "__main__":
    # No clipping (original behavior)
    result = preprocess_images("input_images", "output_images")

    # Symmetric 2% clip on both ends, robust to outlier pixels
    result_clipped = preprocess_images(
        "input_images", "output_images_clipped", clip_percentile=2
    )

    # Asymmetric clip, e.g. ignore bottom 1% but keep top range intact
    result_asym = preprocess_images(
        "input_images", "output_images_asym", clip_percentile=(1, 99.5)
    )

    for fname, s in result_clipped.items():
        print(f"{fname}: {s}")