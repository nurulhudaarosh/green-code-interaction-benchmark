import os
import cv2
import numpy as np

def preprocess_images(input_dir: str, output_dir: str) -> dict:
    """
    Grayscales and min-max normalizes every image in input_dir to the range [0, 255],
    saves the output as a PNG in output_dir, and returns a dict of original 
    min/max stats per file.
    """
    os.makedirs(output_dir, exist_ok=True)
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
    stats = {}

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue
            
        input_path = os.path.join(input_dir, filename)
        
        # Read image in grayscale mode
        gray_img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
        if gray_img is None:
            continue
            
        orig_min = int(gray_img.min())
        orig_max = int(gray_img.max())
        
        # Record original stats
        stats[filename] = {"min": orig_min, "max": orig_max}
        
        # Min-Max Normalization to [0, 255]
        if orig_max > orig_min:
            # Scale range [orig_min, orig_max] -> [0, 255]
            normalized = ((gray_img - orig_min) / (orig_max - orig_min) * 255.0).astype(np.uint8)
        else:
            # Handle edge case where image is flat (all pixels identical)
            normalized = np.zeros_like(gray_img, dtype=np.uint8)

        # Save normalized image as PNG
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}.png"
        output_path = os.path.join(output_dir, output_filename)
        
        cv2.imwrite(output_path, normalized)

    return stats