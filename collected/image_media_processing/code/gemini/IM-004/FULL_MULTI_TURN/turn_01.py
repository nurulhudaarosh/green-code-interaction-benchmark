import os
from PIL import Image
import numpy as np

def preprocess_images(input_dir: str, output_dir: str) -> dict:
    """
    Grayscales and min-max normalizes all images in input_dir to the [0, 255] range,
    saves them as PNGs in output_dir, and returns original min/max stats per file.
    """
    os.makedirs(output_dir, exist_ok=True)
    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')
    stats = {}

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        input_path = os.path.join(input_dir, filename)
        
        with Image.open(input_path) as img:
            # Convert to grayscale ('L' mode: 8-bit pixels, black and white)
            gray_img = img.convert('L')
            arr = np.array(gray_img, dtype=np.float32)

            orig_min = float(arr.min())
            orig_max = float(arr.max())
            stats[filename] = {"min": orig_min, "max": orig_max}

            # Min-Max Normalization to [0, 255] range
            if orig_max > orig_min:
                normalized = (arr - orig_min) / (orig_max - orig_min) * 255.0
            else:
                # Handle uniform color images (prevent division by zero)
                normalized = np.zeros_like(arr)

            normalized_img = Image.fromarray(normalized.astype(np.uint8))

            # Prepare PNG output path
            base_name = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{base_name}.png")
            normalized_img.save(output_path, format="PNG")

    return stats