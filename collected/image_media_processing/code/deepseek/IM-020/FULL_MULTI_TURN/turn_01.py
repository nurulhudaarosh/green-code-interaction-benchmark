import os
from pathlib import Path
import numpy as np
from PIL import Image


# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}

# Classification thresholds (0-255 scale)
DARK_THRESHOLD = 85      # below this -> dark
BRIGHT_THRESHOLD = 170   # above this -> bright
# between -> normal


def analyze_brightness(input_dir):
    """
    Analyze brightness of every image in a directory.

    For each image, computes:
      - per-channel means (R, G, B)
      - overall grayscale brightness (luminance)
      - classification: 'dark', 'normal', or 'bright'

    Args:
        input_dir (str | Path): Directory containing images.

    Returns:
        list[dict]: One record per image with keys:
            'file', 'path', 'r_mean', 'g_mean', 'b_mean',
            'grayscale_brightness', 'classification'
    """
    input_path = Path(input_dir)

    if not input_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    results = []

    # Iterate over files in sorted order for deterministic output
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
            # Don't let one bad image kill the whole run
            print(f"[WARN] Failed to analyze {file_path.name}: {exc}")

    return results


def _analyze_single_image(file_path):
    """Compute brightness metrics for a single image file."""
    with Image.open(file_path) as img:
        # Handle formats with transparency / palette modes by converting to RGB
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        arr = np.asarray(img, dtype=np.float64)  # shape (H, W, 3)

    if arr.ndim == 2:
        # Grayscale image that somehow didn't convert — replicate channels
        arr = np.stack([arr] * 3, axis=-1)

    # Per-channel means
    r_mean = float(arr[:, :, 0].mean())
    g_mean = float(arr[:, :, 1].mean())
    b_mean = float(arr[:, :, 2].mean())

    # Perceptual grayscale brightness (ITU-R BT.601 luma weights)
    grayscale = 0.299 * r_mean + 0.587 * g_mean + 0.114 * b_mean

    # Classification
    if grayscale < DARK_THRESHOLD:
        classification = "dark"
    elif grayscale > BRIGHT_THRESHOLD:
        classification = "bright"
    else:
        classification = "normal"

    return {
        "file": file_path.name,
        "path": str(file_path),
        "r_mean": round(r_mean, 2),
        "g_mean": round(g_mean, 2),
        "b_mean": round(b_mean, 2),
        "grayscale_brightness": round(grayscale, 2),
        "classification": classification,
    }


# ----------------------------------------------------------------------
# Example usage / CLI
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import json

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    records = analyze_brightness(target)

    print(f"\nAnalyzed {len(records)} image(s) in '{target}':\n")
    for r in records:
        print(
            f"  {r['file']:<30} "
            f"R={r['r_mean']:>6.2f}  G={r['g_mean']:>6.2f}  B={r['b_mean']:>6.2f}  "
            f"gray={r['grayscale_brightness']:>6.2f}  -> {r['classification']}"
        )

    # Optional: dump JSON
    # print(json.dumps(records, indent=2))