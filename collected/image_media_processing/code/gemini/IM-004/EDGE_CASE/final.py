import os
import cv2
import numpy as np

def preprocess_images(input_dir, output_dir):
    """
    Reads images from input_dir, converts them to grayscale,
    min-max normalizes pixel values to full 0-255 range,
    saves the processed images as PNGs in output_dir,
    and returns a dictionary with the original min/max stats per file.
    """
    os.makedirs(output_dir, exist_ok=True)
    stats = {}

    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)
        
        # Read image
        img = cv2.imread(input_path)
        if img is None:
            continue
            
        # Convert to grayscale if it is in color
        if len(img.shape) == 3 and img.shape[2] == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Record original min and max pixel values
        orig_min = int(gray.min())
        orig_max = int(gray.max())
        stats[filename] = {"orig_min": orig_min, "orig_max": orig_max}

        # Min-max normalize to 0-255 range
        if orig_max > orig_min:
            normalized = ((gray.astype(np.float32) - orig_min) / (orig_max - orig_min) * 255.0).astype(np.uint8)
        else:
            # Handle flat images (orig_max == orig_min) including all-zero and all-255
            normalized = gray.astype(np.uint8)

        # Save output image as PNG
        base_name, _ = os.path.splitext(filename)
        output_filename = f"{base_name}.png"
        output_path = os.path.join(output_dir, output_filename)
        
        cv2.imwrite(output_path, normalized)

    return stats