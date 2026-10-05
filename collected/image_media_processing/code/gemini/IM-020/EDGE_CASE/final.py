import os
import cv2
import numpy as np
import pandas as pd

def analyze_brightness(input_dir, dark_threshold=85, bright_threshold=170):
    """
    Analyzes images in input_dir for channel means, grayscale brightness,
    and classifies them as 'Dark', 'Normal', or 'Bright'.

    Handles color (3-channel) and grayscale/monochrome (1-channel) images, 
    including half-black half-white checkerboards (mean = 127.5).
    """
    valid_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
    results = []

    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Directory '{input_dir}' does not exist.")

    for filename in sorted(os.listdir(input_dir)):
        if filename.lower().endswith(valid_exts):
            filepath = os.path.join(input_dir, filename)
            
            # Read image as-is (preserves original channels)
            img = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
            if img is None:
                continue

            # Standardize channels: convert 4-channel BGRA to BGR if needed
            if img.ndim == 3 and img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # Compute channel means and grayscale version
            if img.ndim == 2:  # Single-channel grayscale / binary image
                b_mean = g_mean = r_mean = float(np.mean(img))
                gray = img
            else:  # 3-channel BGR image
                b_mean, g_mean, r_mean = cv2.mean(img)[:3]
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Calculate overall grayscale brightness (exact mean across all pixels)
            overall_brightness = float(np.mean(gray))

            # Classification logic
            if overall_brightness < dark_threshold:
                label = 'Dark'
            elif overall_brightness > bright_threshold:
                label = 'Bright'
            else:
                label = 'Normal'

            results.append({
                'Filename': filename,
                'R_Mean': round(r_mean, 2),
                'G_Mean': round(g_mean, 2),
                'B_Mean': round(b_mean, 2),
                'Grayscale_Brightness': round(overall_brightness, 2),
                'Category': label
            })

    return pd.DataFrame(results)