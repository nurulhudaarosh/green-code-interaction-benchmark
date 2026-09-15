import os
from pathlib import Path

import numpy as np
from PIL import Image


def preprocess_images(input_dir, output_dir, clip_percentile=None):
    """
    Grayscale and min-max normalize every image in input_dir to the full 0-255 range,
    save as PNG in output_dir, and return per-file original min/max stats.

    Args:
        input_dir (str | Path): Directory containing input images.
        output_dir (str | Path): Directory to save processed PNGs.
        clip_percentile (float | None): If provided, must be in [0, 50). Pixel values
            below the ``clip_percentile``-th percentile and above the
            ``(100 - clip_percentile)``-th percentile are clipped to those percentile
            bounds before computing the min/max used for normalization. This makes
            the normalization robust to outlier pixels. ``None`` (default) uses the
            true min/max of the image.

    Returns:
        dict: Mapping of filename -> {
            "original_min": int,
            "original_max": int,
            "clip_min": int | None,
            "clip_max": int | None,
        }
        ``original_min``/``original_max`` are the true data extremes; ``clip_min``/
        ``clip_max`` are the percentile bounds actually used for normalization
        (both ``None`` when ``clip_percentile`` is not set).
    """
    if clip_percentile is not None:
        if not (0 <= clip_percentile < 50):
            raise ValueError(
                f"clip_percentile must be in [0, 50), got {clip_percentile!r}"
            )

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

        # Determine the bounds used for normalization.
        if clip_percentile is not None and clip_percentile > 0:
            lo = np.percentile(arr, clip_percentile)
            hi = np.percentile(arr, 100.0 - clip_percentile)
            # Snap to integers so the reported stats are consistent with the data
            # range (pixel values are integers 0-255).
            clip_min = int(np.floor(lo))
            clip_max = int(np.ceil(hi))
        else:
            clip_min = orig_min
            clip_max = orig_max

        # Min-max normalize to 0-255 using the (possibly clipped) bounds.
        if clip_max > clip_min:
            normalized = (arr - clip_min) / (clip_max - clip_min) * 255.0
        else:
            # Constant image (or degenerate clip range): map everything to 0.
            normalized = np.zeros_like(arr)

        normalized = np.clip(normalized, 0, 255).astype(np.uint8)

        # Save as PNG (stem preserved, extension forced to .png)
        out_path = output_dir / (img_path.stem + ".png")
        Image.fromarray(normalized, mode="L").save(out_path, format="PNG")

        stats[img_path.name] = {
            "original_min": orig_min,
            "original_max": orig_max,
            "clip_min": clip_min if clip_percentile is not None else None,
            "clip_max": clip_max if clip_percentile is not None else None,
        }

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    parser.add_argument(
        "--clip-percentile",
        type=float,
        default=None,
        help="Clip this percentage from each tail before normalization (e.g. 1).",
    )
    args = parser.parse_args()

    result = preprocess_images(
        args.input_dir, args.output_dir, clip_percentile=args.clip_percentile
    )
    for name, s in result.items():
        extra = ""
        if s["clip_min"] is not None:
            extra = f", clipped to [{s['clip_min']}, {s['clip_max']}]"
        print(
            f"{name}: original min={s['original_min']}, max={s['original_max']}{extra}"
        )