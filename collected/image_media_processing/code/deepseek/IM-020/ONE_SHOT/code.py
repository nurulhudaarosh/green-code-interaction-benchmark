import os
import cv2
import numpy as np


def analyze_brightness(input_dir, dark_threshold=85, bright_threshold=170):
    """
    Analyze brightness of all images in a directory.

    Args:
        input_dir (str): Directory containing images.
        dark_threshold (float): Grayscale mean below this is 'dark'.
        bright_threshold (float): Grayscale mean above this is 'bright'.

    Returns:
        list[dict]: One entry per image with keys:
            - filename
            - mean_b, mean_g, mean_r (per-channel means, 0-255)
            - gray_brightness (overall luminance, 0-255)
            - classification ('dark' | 'normal' | 'bright')
    """
    valid_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp')
    results = []

    if not os.path.isdir(input_dir):
        raise ValueError(f"Not a directory: {input_dir}")

    for filename in sorted(os.listdir(input_dir)):
        if not filename.lower().endswith(valid_exts):
            continue

        filepath = os.path.join(input_dir, filename)
        img = cv2.imread(filepath, cv2.IMREAD_COLOR)  # loads as BGR
        if img is None:
            print(f"Warning: could not read {filepath}")
            continue

        # Per-channel means (BGR order)
        mean_b = float(np.mean(img[:, :, 0]))
        mean_g = float(np.mean(img[:, :, 1]))
        mean_r = float(np.mean(img[:, :, 2]))

        # Overall grayscale brightness (luminance-weighted, perceptual)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_brightness = float(np.mean(gray))

        # Classification
        if gray_brightness < dark_threshold:
            classification = 'dark'
        elif gray_brightness > bright_threshold:
            classification = 'bright'
        else:
            classification = 'normal'

        results.append({
            'filename': filename,
            'mean_b': round(mean_b, 2),
            'mean_g': round(mean_g, 2),
            'mean_r': round(mean_r, 2),
            'gray_brightness': round(gray_brightness, 2),
            'classification': classification,
        })

    return results


# -------- Example usage --------
if __name__ == '__main__':
    import sys
    import json

    directory = sys.argv[1] if len(sys.argv) > 1 else './images'
    report = analyze_brightness(directory)

    print(f"{'File':<30}{'B':>7}{'G':>7}{'R':>7}{'Gray':>8}  Class")
    print('-' * 70)
    for r in report:
        print(f"{r['filename']:<30}{r['mean_b']:>7}{r['mean_g']:>7}"
              f"{r['mean_r']:>7}{r['gray_brightness']:>8}  {r['classification']}")

    # Optionally dump to JSON
    # with open('brightness_report.json', 'w') as f:
    #     json.dump(report, f, indent=2)