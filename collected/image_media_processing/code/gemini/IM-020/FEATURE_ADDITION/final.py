import os
from typing import Optional, Tuple
import cv2
import numpy as np
import pandas as pd


def analyze_brightness(
    input_dir: str,
    custom_thresholds: Optional[Tuple[float, float]] = None,
) -> pd.DataFrame:
    """Analyzes brightness for all images in a given directory.

    Args:
        input_dir (str): Directory containing image files.
        custom_thresholds (Optional[Tuple[float, float]]): Optional tuple of
          (dark_max, bright_min) to set custom classification boundaries.
          Defaults to (85.0, 170.0).

    Returns:
        pd.DataFrame: Table with filename, per-channel means, overall
        brightness, and classification.
    """
    if custom_thresholds is not None:
        if len(custom_thresholds) != 2:
            raise ValueError(
                "custom_thresholds must be a tuple of 2 floats/ints: (dark_max, bright_min)"
            )
        dark_max, bright_min = custom_thresholds
        if dark_max >= bright_min:
            raise ValueError(
                f"dark_max ({dark_max}) must be strictly less than bright_min ({bright_min})"
            )
    else:
        dark_max, bright_min = 85.0, 170.0

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    results = []

    if not os.path.isdir(input_dir):
        raise ValueError(f"Directory not found: {input_dir}")

    for filename in sorted(os.listdir(input_dir)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue

        filepath = os.path.join(input_dir, filename)
        img_bgr = cv2.imread(filepath)

        if img_bgr is None:
            print(f"Warning: Could not read image '{filename}'. Skipping.")
            continue

        # Compute per-channel means (OpenCV loads BGR, extract RGB)
        b_mean, g_mean, r_mean = cv2.mean(img_bgr)[:3]

        # Convert to Grayscale for overall perceptual brightness
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        overall_brightness = float(np.mean(img_gray))

        # Classify brightness using specified boundaries
        if overall_brightness < dark_max:
            classification = "Dark"
        elif overall_brightness > bright_min:
            classification = "Bright"
        else:
            classification = "Normal"

        results.append(
            {
                "filename": filename,
                "red_mean": round(r_mean, 2),
                "green_mean": round(g_mean, 2),
                "blue_mean": round(b_mean, 2),
                "overall_brightness": round(overall_brightness, 2),
                "classification": classification,
            }
        )

    return pd.DataFrame(results)


# Examples of usage:
if __name__ == "__main__":
    image_directory = "./images"

    # 1. Standard usage (uses default 85.0 and 170.0)
    df_default = analyze_brightness(image_directory)

    # 2. Custom threshold usage
    df_custom = analyze_brightness(
        image_directory, custom_thresholds=(60.0, 200.0)
    )