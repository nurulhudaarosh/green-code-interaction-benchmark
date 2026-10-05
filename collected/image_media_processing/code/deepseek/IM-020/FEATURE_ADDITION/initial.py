import os
from pathlib import Path
from typing import Dict, List, Union

import numpy as np
from PIL import Image


# Classification thresholds (0-255 scale)
DARK_THRESHOLD = 85      # below this -> "dark"
BRIGHT_THRESHOLD = 170   # above this -> "bright"
# between -> "normal"

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def _classify(brightness: float,
              dark_threshold: float = DARK_THRESHOLD,
              bright_threshold: float = BRIGHT_THRESHOLD) -> str:
    """Map a grayscale brightness value to a label."""
    if brightness < dark_threshold:
        return "dark"
    if brightness > bright_threshold:
        return "bright"
    return "normal"


def analyze_brightness(input_dir: Union[str, Path],
                       recursive: bool = False,
                       dark_threshold: float = DARK_THRESHOLD,
                       bright_threshold: float = BRIGHT_THRESHOLD) -> List[Dict]:
    """
    Analyze brightness of every image in `input_dir`.

    Parameters
    ----------
    input_dir : str | Path
        Directory containing images.
    recursive : bool
        If True, walk subdirectories as well.
    dark_threshold, bright_threshold : float
        Grayscale cutoffs (0-255) for the dark/normal/bright labels.

    Returns
    -------
    list of dict, one per image, each containing:
        - file:               absolute path to the image
        - name:               filename
        - mean_r, mean_g, mean_b: per-channel means (0-255)
        - brightness:         overall grayscale brightness (0-255)
        - classification:     "dark" | "normal" | "bright"
        - error:              present only if the image could not be read
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    # Collect image paths
    if recursive:
        candidates = (p for p in input_dir.rglob("*") if p.is_file())
    else:
        candidates = (p for p in input_dir.iterdir() if p.is_file())

    image_paths = sorted(
        p for p in candidates if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    results: List[Dict] = []

    for path in image_paths:
        try:
            with Image.open(path) as img:
                # Convert to RGB so modes like L, P, RGBA, CMYK all work
                rgb = img.convert("RGB")
                arr = np.asarray(rgb, dtype=np.float32)  # shape: H x W x 3

            mean_r = float(arr[..., 0].mean())
            mean_g = float(arr[..., 1].mean())
            mean_b = float(arr[..., 2].mean())

            # Grayscale brightness via Rec. 709 luma weights
            brightness = (
                0.2126 * mean_r +
                0.7152 * mean_g +
                0.0722 * mean_b
            )

            results.append({
                "file": str(path.resolve()),
                "name": path.name,
                "mean_r": round(mean_r, 2),
                "mean_g": round(mean_g, 2),
                "mean_b": round(mean_b, 2),
                "brightness": round(brightness, 2),
                "classification": _classify(
                    brightness, dark_threshold, bright_threshold
                ),
            })

        except Exception as exc:  # unreadable / corrupt files
            results.append({
                "file": str(path.resolve()),
                "name": path.name,
                "error": f"{type(exc).__name__}: {exc}",
            })

    return results


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    report = analyze_brightness(target, recursive=True)

    for entry in report:
        if "error" in entry:
            print(f"[ERR ] {entry['name']}: {entry['error']}")
        else:
            print(
                f"[{entry['classification']:>6}] "
                f"{entry['name']:<40} "
                f"R={entry['mean_r']:>6.2f} "
                f"G={entry['mean_g']:>6.2f} "
                f"B={entry['mean_b']:>6.2f} "
                f"brightness={entry['brightness']:>6.2f}"
            )

    print(f"\nAnalyzed {len(report)} image(s) in {target}")