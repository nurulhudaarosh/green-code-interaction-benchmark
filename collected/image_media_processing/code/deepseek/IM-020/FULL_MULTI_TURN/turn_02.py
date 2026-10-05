import os
from pathlib import Path
import numpy as np
from PIL import Image


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}

DARK_THRESHOLD = 85
BRIGHT_THRESHOLD = 170


def analyze_brightness(input_dir):
    """
    Analyze brightness of every image in a directory.

    For each image computes:
      - per-channel means (R, G, B) from the RGB rendering
      - overall grayscale brightness as the mean of the image converted
        to Pillow 'L' mode (perceptual luminance)
      - classification: 'dark', 'normal', or 'bright'
    """
    input_path = Path(input_dir)

    if not input_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    results = []

    for file_path in sorted(input_path.iterdir()):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        try:
            record = _analyze_single_image(file_path)
            if record is not None:
                results.append(record)
        except Exception as exc:
            print(f"[WARN] Failed to analyze {file_path.name}: {exc}")

    return results


def _analyze_single_image(file_path):
    """Compute brightness metrics for a single image file."""
    with Image.open(file_path) as img:
        # RGB version for per-channel means
        rgb_img = img.convert("RGB")
        rgb_arr = np.asarray(rgb_img, dtype=np.float64)  # (H, W, 3)

        # True grayscale conversion: Pillow 'L' mode applies perceptual
        # luminance weighting per pixel (BT.601: 0.299 R + 0.587 G + 0.114 B).
        gray_img = img.convert("L")
        gray_arr = np.asarray(gray_img, dtype=np.float64)  # (H, W)

    # Per-channel means (independent of grayscale conversion)
    r_mean = float(rgb_arr[:, :, 0].mean())
    g_mean = float(rgb_arr[:, :, 1].mean())
    b_mean = float(rgb_arr[:, :, 2].mean())

    # True grayscale brightness: mean of the L-mode image
    grayscale_brightness = float(gray_arr.mean())

    if grayscale_brightness < DARK_THRESHOLD:
        classification = "dark"
    elif grayscale_brightness > BRIGHT_THRESHOLD:
        classification = "bright"
    else:
        classification = "normal"

    return {
        "file": file_path.name,
        "path": str(file_path),
        "r_mean": round(r_mean, 2),
        "g_mean": round(g_mean, 2),
        "b_mean": round(b_mean, 2),
        "grayscale_brightness": round(grayscale_brightness, 2),
        "classification": classification,
    }


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    records = analyze_brightness(target)

    print(f"\nAnalyzed {len(records)} image(s) in '{target}':\n")
    for r in records:
        print(
            f"  {r['file']:<30} "
            f"R={r['r_mean']:>6.2f}  G={r['g_mean']:>6.2f}  B={r['b_mean']:>6.2f}  "
            f"gray={r['grayscale_brightness']:>6.2f}  -> {r['classification']}"
        )