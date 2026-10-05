import os
import glob
import numpy as np
from PIL import Image

def sobel_edges(input_dir, output_dir):
    """
    Applies explicit Sobel edge detection to all images in input_dir
    and saves the clipped gradient magnitude images as grayscale PNGs in output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Standard 3x3 Sobel kernels for horizontal (Gx) and vertical (Gy) gradients
    Gx = np.array([
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ], dtype=np.float32)

    Gy = np.array([
        [-1, -2, -1],
         [0,  0,  0],
         [1,  2,  1]
    ], dtype=np.float32)

    # Supported image extensions
    extensions = ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff")
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(input_dir, ext)))

    for path in image_paths:
        # Load image and convert to 2D grayscale float array [0, 255]
        img = Image.open(path).convert('L')
        img_arr = np.array(img, dtype=np.float32)

        # Pad image borders by 1 pixel using reflection to handle boundary convolution
        padded = np.pad(img_arr, pad_width=1, mode='reflect')
        h, w = img_arr.shape

        # Extract 3x3 sliding windows
        windows = np.lib.stride_tricks.sliding_window_view(padded, (3, 3))

        # Explicit convolution via element-wise multiplication and summation over 3x3 windows
        grad_x = np.sum(windows * Gx, axis=(-2, -1))
        grad_y = np.sum(windows * Gy, axis=(-2, -1))

        # Compute gradient magnitude: sqrt(Gx^2 + Gy^2)
        magnitude = np.sqrt(grad_x**2 + grad_y**2)

        # Clip values to [0, 255] range and convert to uint8
        magnitude_clipped = np.clip(magnitude, 0, 255).astype(np.uint8)

        # Save result as grayscale PNG
        base_name = os.path.splitext(os.path.basename(path))[0]
        out_path = os.path.join(output_dir, f"{base_name}_sobel.png")
        Image.fromarray(magnitude_clipped).save(out_path)