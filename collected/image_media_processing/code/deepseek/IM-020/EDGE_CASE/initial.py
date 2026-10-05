import os
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
from PIL import Image

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}

# Classification thresholds (0-255 grayscale scale)
DARK_THRESHOLD = 85      # < 85  -> dark
BRIGHT_THRESHOLD = 170   # > 170 -> bright
                         # otherwise -> normal


def analyze_brightness(input_dir: str) -> List[Dict[str, Any]]:
    """
    Analyze the brightness of every image in `input_dir`.

    For each image, computes:
      - per-channel means (R, G, B) on a 0-255 scale
      - overall grayscale brightness (luminance-weighted, 0-255)
      - classification: "dark", "normal", or "bright"

    Parameters
    ----------
    input_dir : str
        Path to a directory containing image files.

    Returns
    -------
    list of dict
        One dict per image with keys:
            file, red_mean, green_mean, blue_mean,
            grayscale_brightness, classification
        Sorted by filename. Returns an empty list if no images are found.

    Raises
    ------
    NotADirectoryError
        If `input_dir` is not a valid directory.
    """
    directory = Path(input_dir)
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    results: List[Dict[str, Any]] = []

    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        try:
            # Convert to RGB to normalize modes (grayscale, RGBA, CMYK, palette, etc.)
            with Image.open(path) as img:
                rgb = img.convert("RGB")
                arr = np.asarray(rgb, dtype=np.float32)  # shape: (H, W, 3)
        except (OSError, ValueError) as e:
            # Skip unreadable / corrupt images but keep going
            results.append({
                "file": path.name,
                "error": str(e),
            })
            continue

        # Per-channel means (0-255)
        r_mean = float(arr[:, :, 0].mean())
        g_mean = float(arr[:, :, 1].mean())
        b_mean = float(arr[:, :, 2].mean())

        # Perceptual grayscale (Rec. 709 luma coefficients)
        grayscale = 0.2126 * r_mean + 0.7152 * g_mean + 0.0722 * b_mean

        # Classification
        if grayscale < DARK_THRESHOLD:
            classification = "dark"
        elif grayscale > BRIGHT_THRESHOLD:
            classification = "bright"
        else:
            classification = "normal"

        results.append({
            "file": path.name,
            "red_mean": round(r_mean, 2),
            "green_mean": round(g_mean, 2),
            "blue_mean": round(b_mean, 2),
            "grayscale_brightness": round(grayscale, 2),
            "classification": classification,
        })

    return results


# ---------------------------------------------------------------------------
# Demo / CLI usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import json

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    report = analyze_brightness(target)

    if not report:
        print(f"No images found in: {target}")
    else:
        print(json.dumps(report, indent=2))

        # Quick summary
        counts = {"dark": 0, "normal": 0, "bright": 0}
        for entry in report:
            if "classification" in entry:
                counts[entry["classification"]] += 1
        print(f"\nSummary: {counts}")