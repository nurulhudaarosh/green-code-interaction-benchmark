import os
import cv2
import pandas as pd


def analyze_brightness(
    input_dir: str, dark_thresh: float = 85.0, bright_thresh: float = 170.0
) -> pd.DataFrame:
    """Analyzes brightness metrics and classifies images in a directory.

    Args:
        input_dir: Path to directory containing images.
        dark_thresh: Grayscale mean threshold below which an image is 'dark'.
        bright_thresh: Grayscale mean threshold above which an image is 'bright'.

    Returns:
        pd.DataFrame containing per-channel means, overall brightness, and
        classifications.
    """
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    results = []

    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Directory not found: {input_dir}")

    for filename in sorted(os.listdir(input_dir)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue

        file_path = os.path.join(input_dir, filename)
        # Read image in BGR color space
        img = cv2.imread(file_path)

        if img is None:
            continue

        # OpenCV imread returns images in BGR order
        mean_b, mean_g, mean_r = img.mean(axis=(0, 1))

        # Standard ITU-R BT.601 luminance calculation for grayscale conversion
        mean_gray = 0.299 * mean_r + 0.587 * mean_g + 0.114 * mean_b

        # Classification
        if mean_gray < dark_thresh:
            label = "dark"
        elif mean_gray > bright_thresh:
            label = "bright"
        else:
            label = "normal"

        results.append(
            {
                "filename": filename,
                "mean_red": round(float(mean_r), 2),
                "mean_green": round(float(mean_g), 2),
                "mean_blue": round(float(mean_b), 2),
                "mean_brightness": round(float(mean_gray), 2),
                "classification": label,
            }
        )

    return pd.DataFrame(results)