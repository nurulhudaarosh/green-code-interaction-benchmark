"""Image brightness analysis.

Usage:
    python analyze_brightness.py INPUT_DIR [--csv out.csv] [--recursive]

Requires: Pillow, numpy  (pip install pillow numpy)
"""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}

# Thresholds on the 0-255 grayscale mean.
DARK_MAX = 85      # brightness <  85        -> "dark"
BRIGHT_MIN = 170   # brightness >= 170       -> "bright"; otherwise "normal"

def classify(brightness, dark_max=DARK_MAX, bright_min=BRIGHT_MIN):
    if brightness < dark_max:
        return "dark"
    if brightness >= bright_min:
        return "bright"
    return "normal"


def _load(path):
    """Load an image and return (rgb_pixels, gray_pixels) as float arrays.

    Transparent images are composited onto white. The grayscale array comes
    from Pillow's true 'L' mode conversion (perceptual luminance weighting).
    """
    with Image.open(path) as img:
        img.load()
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            rgba = img.convert("RGBA")
            background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            rgb_img = Image.alpha_composite(background, rgba).convert("RGB")
        else:
            rgb_img = img.convert("RGB")
        gray_img = rgb_img.convert("L")
        return (
            np.asarray(rgb_img, dtype=np.float64),
            np.asarray(gray_img, dtype=np.float64),
        )


def analyze_brightness(input_dir, recursive=False, dark_max=DARK_MAX, bright_min=BRIGHT_MIN):
    """Analyze every image in `input_dir`.

    Returns a list of dicts, one per image, sorted by filename:
        {
          "filename": str,
          "mean_r": float, "mean_g": float, "mean_b": float,   # 0-255
          "brightness": float,                                  # grayscale mean, 0-255
          "category": "dark" | "normal" | "bright",
        }
    Files that can't be read as images get {"filename", "error"} instead.
    """
    root = Path(input_dir)
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    pattern = "**/*" if recursive else "*"
    files = sorted(
        p for p in root.glob(pattern)
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    results = []
    for path in files:
        name = str(path.relative_to(root))
        try:
            pixels, gray = _load(path)
        except Exception as exc:  # corrupt / unsupported file
            results.append({"filename": name, "error": str(exc)})
            continue

        mean_r, mean_g, mean_b = pixels.reshape(-1, 3).mean(axis=0)
        brightness = float(gray.mean())
        results.append({
            "filename": name,
            "mean_r": round(float(mean_r), 2),
            "mean_g": round(float(mean_g), 2),
            "mean_b": round(float(mean_b), 2),
            "brightness": round(brightness, 2),
            "category": classify(brightness, dark_max, bright_min),
        })
    return results


def _main():
    parser = argparse.ArgumentParser(description="Per-image brightness analysis.")
    parser.add_argument("input_dir")
    parser.add_argument("--csv", help="Write results to this CSV file")
    parser.add_argument("--recursive", action="store_true", help="Include subfolders")
    args = parser.parse_args()

    results = analyze_brightness(args.input_dir, recursive=args.recursive)
    if not results:
        print("No images found.", file=sys.stderr)
        return 1

    header = f"{'file':40} {'R':>7} {'G':>7} {'B':>7} {'gray':>7}  class"
    print(header)
    print("-" * len(header))
    for r in results:
        if "error" in r:
            print(f"{r['filename'][:40]:40} ERROR: {r['error']}")
        else:
            print(f"{r['filename'][:40]:40} {r['mean_r']:7.2f} {r['mean_g']:7.2f} "
                  f"{r['mean_b']:7.2f} {r['brightness']:7.2f}  {r['category']}")

    if args.csv:
        fields = ["filename", "mean_r", "mean_g", "mean_b", "brightness", "category", "error"]
        with open(args.csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nSaved {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())