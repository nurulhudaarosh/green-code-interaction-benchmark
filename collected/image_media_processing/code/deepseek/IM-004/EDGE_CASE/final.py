import os
import cv2
import numpy as np


def preprocess_images(input_dir, output_dir):
    """
    Grayscale and min-max normalize every image in input_dir to full 0-255 range,
    save as PNG in output_dir, and return original min/max stats per file.

    Edge cases handled:
        - Fully black image (all zeros): orig_min == orig_max == 0 -> kept as all zeros.
        - Fully white image (all 255):  orig_min == orig_max == 255 -> kept as all 255.
        - Any other constant image: preserved at its original constant value.
        - 16-bit / non-8-bit inputs: handled without overflow.

    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory to save preprocessed PNG images.

    Returns:
        dict: {filename: {"orig_min": int, "orig_max": int, "flat": bool}}
    """
    os.makedirs(output_dir, exist_ok=True)
    stats = {}

    valid_exts = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp")

    for filename in sorted(os.listdir(input_dir)):
        if not filename.lower().endswith(valid_exts):
            continue

        in_path = os.path.join(input_dir, filename)
        img = cv2.imread(in_path, cv2.IMREAD_UNCHANGED)

        if img is None:
            print(f"[WARN] Could not read {in_path}, skipping.")
            continue

        # Convert to grayscale (handles BGR, BGRA, and already-gray images)
        if img.ndim == 3:
            if img.shape[2] == 4:
                gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            else:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        orig_min = int(gray.min())
        orig_max = int(gray.max())
        is_flat = (orig_max == orig_min)

        if is_flat:
            # Flat image (includes all-black and all-white).
            # Normalization is undefined; preserve the original constant value
            # so all-black stays 0 and all-white stays 255.
            norm = np.full_like(gray, orig_min, dtype=np.uint8)
        else:
            # Min-max normalize to 0-255
            norm = (gray.astype(np.float32) - orig_min) / (orig_max - orig_min)
            norm = (norm * 255.0).round().astype(np.uint8)

        out_name = os.path.splitext(filename)[0] + ".png"
        out_path = os.path.join(output_dir, out_name)
        cv2.imwrite(out_path, norm)

        stats[filename] = {
            "orig_min": orig_min,
            "orig_max": orig_max,
            "flat": is_flat,
        }

    return stats