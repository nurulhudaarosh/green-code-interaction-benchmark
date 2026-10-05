import os
import cv2
import numpy as np
import pandas as pd

def analyze_brightness(input_dir, dark_threshold=85, bright_threshold=170):
    """
    Analyzes all images in input_dir for channel means, grayscale brightness,
    and classifies them as 'Dark', 'Normal', or 'Bright'.

    Parameters:
        input_dir (str): Path to directory containing images.
        dark_threshold (float): Upper mean grayscale bound for 'Dark' images (0-255).
        bright_threshold (float): Lower mean grayscale bound for 'Bright' images (0-255).

    Returns:
        pd.DataFrame: Table with image names, RGB channel means, grayscale mean, and label.
    """
    valid_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
    results = []

    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Directory '{input_dir}' does not exist.")

    for filename in sorted(os.listdir(input_dir)):
        if filename.lower().endswith(valid_exts):
            filepath = os.path.join(input_dir, filename)
            
            # Read image using OpenCV (loads in BGR format)
            img = cv2.imread(filepath)
            if img is None:
                continue

            # Compute channel-wise mean (BGR)
            b_mean, g_mean, r_mean = cv2.mean(img)[:3]

            # Convert to Grayscale & calculate overall brightness
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
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