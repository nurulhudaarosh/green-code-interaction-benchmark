"""Brightness analysis for a folder of images.

Usage:
    python analyze_brightness.py path/to/images [--dark 85] [--bright 170]

Requires: Pillow, numpy
"""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}

# Thresholds on the 0-255 grayscale mean.
DARK_THRESHOLD = 85      # below this -> "dark"
BRIGHT_THRESHOLD = 170   # above this -> "bright"; in between -> "normal"

# ITU-R BT.601 luma weights, the standard RGB -> grayscale conversion.
LUMA_WEIGHTS = np.array([0.299, 0.587, 0.114])
LUMA_WEIGHTS = LUMA_WEIGHTS / LUMA_WEIGHTS.sum()  # guard against float drift: gray stays gray


def classify(brightness, dark=DARK_THRESHOLD, bright=BRIGHT_THRESHOLD):
    """Map a 0-255 brightness value to 'dark', 'normal' or 'bright'."""
    if brightness < dark:
        return "dark"
    if brightness > bright:
        return "bright"
    return "normal"


def analyze_brightness(input_dir, dark=DARK_THRESHOLD, bright=BRIGHT_THRESHOLD, recursive=False):
    """Analyze every image in `input_dir`.

    Returns a list of dicts (sorted by file name), one per image:
        {
            "file": "photo.jpg",
            "mean_r": float, "mean_g": float, "mean_b": float,   # 0-255
            "brightness": float,                                  # grayscale mean, 0-255
            "category": "dark" | "normal" | "bright",
        }
    Files that cannot be read as images get {"file": ..., "error": "..."} instead.
    """
    input_path = Path(input_dir)
    if not input_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    pattern = "**/*" if recursive else "*"
    files = sorted(
        p for p in input_path.glob(pattern)
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    results = []
    for path in files:
        name = str(path.relative_to(input_path))
        try:
            with Image.open(path) as img:
                # Flatten transparency onto black so alpha doesn't skew the means.
                if img.mode in ("RGBA", "LA") or "transparency" in img.info:
                    rgba = img.convert("RGBA")
                    background = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
                    img = Image.alpha_composite(background, rgba)
                rgb = np.asarray(img.convert("RGB"), dtype=np.float64)
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            results.append({"file": name, "error": str(exc)})
            continue

        mean_r, mean_g, mean_b = rgb.reshape(-1, 3).mean(axis=0)
        brightness = float(np.dot([mean_r, mean_g, mean_b], LUMA_WEIGHTS))

        results.append({
            "file": name,
            "mean_r": round(float(mean_r), 2),
            "mean_g": round(float(mean_g), 2),
            "mean_b": round(float(mean_b), 2),
            "brightness": round(brightness, 2),
            "category": classify(brightness, dark, bright),
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="Per-image brightness analysis.")
    parser.add_argument("input_dir")
    parser.add_argument("--dark", type=float, default=DARK_THRESHOLD)
    parser.add_argument("--bright", type=float, default=BRIGHT_THRESHOLD)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    args = parser.parse_args()

    results = analyze_brightness(args.input_dir, args.dark, args.bright, args.recursive)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"{'file':<40} {'R':>7} {'G':>7} {'B':>7} {'bright':>8}  category")
    for r in results:
        if "error" in r:
            print(f"{r['file']:<40} ERROR: {r['error']}")
        else:
            print(f"{r['file']:<40} {r['mean_r']:>7.1f} {r['mean_g']:>7.1f} "
                  f"{r['mean_b']:>7.1f} {r['brightness']:>8.1f}  {r['category']}")


if __name__ == "__main__":
    main()