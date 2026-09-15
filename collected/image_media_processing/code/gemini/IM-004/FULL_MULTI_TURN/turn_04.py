import os
from PIL import Image
import numpy as np

def preprocess_images(input_dir: str, output_dir: str) -> dict:
    """
    Grayscales and min-max normalizes all images in input_dir to the [0, 255] range,
    saves them as PNGs in output_dir, and returns original min/max stats per file.
    
    Handles flat/uniform images (all-black, all-white, or any single-color image)
    without ZeroDivisionError by preserving their native pixel values.
    """
    os.makedirs(output_dir, exist_ok=True)
    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')
    stats = {}

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        input_path = os.path.join(input_dir, filename)
        
        with Image.open(input_path) as img:
            # Convert image to 8-bit grayscale ('L' mode)
            gray_img = img.convert('L')
            arr = np.array(gray_img, dtype=np.float32)

            orig_min = float(arr.min())
            orig_max = float(arr.max())
            stats[filename] = {"min": orig_min, "max": orig_max}

            # Check for zero contrast (all pixels are identical)
            if orig_max == orig_min:
                # All-black (0.0), all-white (255.0), or any solid shade stays unchanged
                normalized = arr
            else:
                # Standard Min-Max Normalization to [0, 255]
                normalized = (arr - orig_min) / (orig_max - orig_min) * 255.0

            # Convert back to uint8 array and save as PNG
            normalized_img = Image.fromarray(np.clip(normalized, 0, 255).astype(np.uint8))

            base_name = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{base_name}.png")
            normalized_img.save(output_path, format="PNG")

    return stats