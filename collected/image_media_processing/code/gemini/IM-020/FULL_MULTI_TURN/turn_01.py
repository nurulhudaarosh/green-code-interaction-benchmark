from pathlib import Path
import cv2
import numpy as np


def analyze_brightness(
    input_dir: str | Path,
    dark_threshold: float = 85.0,
    bright_threshold: float = 170.0,
) -> list[dict]:
    """Analyzes brightness metrics for all valid images in a directory.

    Args:
        input_dir: Path to directory containing images.
        dark_threshold: Grayscale mean threshold below which an image is 'dark'.
        bright_threshold: Grayscale mean threshold above which an image is
          'bright'.

    Returns:
        A list of dictionaries with image stats and classification.
    """
    path = Path(input_dir)
    if not path.is_dir():
        raise ValueError(f"Directory non-existent or invalid: {input_dir}")

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    results = []

    for file_path in sorted(path.iterdir()):
        if file_path.suffix.lower() not in valid_extensions:
            continue

        # Load image (BGR format)
        img = cv2.imread(str(file_path))
        if img is None:
            continue

        # Compute per-channel means (OpenCV uses BGR order)
        b_mean, g_mean, r_mean = cv2.mean(img)[:3]

        # Convert to standard Grayscale to measure perceived luminance
        # Formula: Y = 0.299*R + 0.587*G + 0.114*B
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        grayscale_brightness = float(np.mean(gray))

        # Determine classification
        if grayscale_brightness < dark_threshold:
            classification = "dark"
        elif grayscale_brightness > bright_threshold:
            classification = "bright"
        else:
            classification = "normal"

        results.append(
            {
                "filename": file_path.name,
                "path": str(file_path),
                "means_bgr": {
                    "blue": round(b_mean, 2),
                    "green": round(g_mean, 2),
                    "red": round(r_mean, 2),
                },
                "brightness": round(grayscale_brightness, 2),
                "classification": classification,
            }
        )

    return results


# Example Usage:
if __name__ == "__main__":
    # Replace 'images/' with your target directory path
    image_stats = analyze_brightness("images")

    for stat in image_stats:
        print(f"[{stat['classification'].upper()}] {stat['filename']}")
        print(f"  Overall Brightness: {stat['brightness']} / 255")
        print(f"  Channel Means (RGB): {stat['means_bgr']['red']}, "
              f"{stat['means_bgr']['green']}, {stat['means_bgr']['blue']}\n")