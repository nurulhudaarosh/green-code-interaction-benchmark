import os
from PIL import Image
import numpy as np


def analyze_brightness(input_dir, dark_threshold=85, bright_threshold=170):
    """
    Analyze brightness of all images in a directory.

    Per-channel means come from the RGB channels; overall brightness is the
    mean of the true grayscale ('L' mode) image, which uses perceptual
    luminance weighting rather than an equal-weight average of channels.

    Args:
        input_dir (str): Directory containing images.
        dark_threshold (float): Grayscale mean below this is 'dark'.
        bright_threshold (float): Grayscale mean above this is 'bright'.

    Returns:
        list[dict]: One entry per image with keys:
            - filename
            - mean_r, mean_g, mean_b (per-channel means, 0-255)
            - brightness (mean of 'L'-mode grayscale, 0-255)
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
        try:
            with Image.open(filepath) as im:
                rgb = im.convert('RGB')
                arr = np.asarray(rgb, dtype=np.float32)

                # Per-channel means from the RGB image
                mean_r = float(arr[:, :, 0].mean())
                mean_g = float(arr[:, :, 1].mean())
                mean_b = float(arr[:, :, 2].mean())

                # True grayscale brightness: 'L' mode uses perceptual
                # luminance weighting (0.299 R + 0.587 G + 0.114 B),
                # NOT a simple average of the channel means.
                gray = np.asarray(im.convert('L'), dtype=np.float32)
                brightness = float(gray.mean())
        except (OSError, ValueError) as e:
            print(f"Warning: could not read {filepath}: {e}")
            continue

        if brightness < dark_threshold:
            classification = 'dark'
        elif brightness > bright_threshold:
            classification = 'bright'
        else:
            classification = 'normal'

        results.append({
            'filename': filename,
            'mean_r': round(mean_r, 2),
            'mean_g': round(mean_g, 2),
            'mean_b': round(mean_b, 2),
            'brightness': round(brightness, 2),
            'classification': classification,
        })

    return results


if __name__ == '__main__':
    import sys

    directory = sys.argv[1] if len(sys.argv) > 1 else './images'
    report = analyze_brightness(directory)

    print(f"{'File':<30}{'R':>7}{'G':>7}{'B':>7}{'Bright':>8}  Class")
    print('-' * 70)
    for r in report:
        print(f"{r['filename']:<30}{r['mean_r']:>7}{r['mean_g']:>7}"
              f"{r['mean_b']:>7}{r['brightness']:>8}  {r['classification']}")