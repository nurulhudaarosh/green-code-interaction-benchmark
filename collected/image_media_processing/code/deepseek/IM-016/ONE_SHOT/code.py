import os
import numpy as np
from PIL import Image

def sobel_edges(input_dir, output_dir):
    """
    Apply Sobel edge detection to all images in input_dir and save
    gradient magnitude images to output_dir as grayscale PNGs.
    
    Uses explicit Sobel kernels for Gx and Gy convolution.
    """
    # Sobel kernels
    Gx = np.array([[1, 0, -1],
                   [2, 0, -2],
                   [1, 0, -1]], dtype=np.float32)
    
    Gy = np.array([[ 1,  2,  1],
                   [ 0,  0,  0],
                   [-1, -2, -1]], dtype=np.float32)
    
    os.makedirs(output_dir, exist_ok=True)
    
    valid_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')
    
    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(valid_exts):
            continue
        
        in_path = os.path.join(input_dir, fname)
        
        # Load as grayscale, float32
        img = Image.open(in_path).convert('L')
        arr = np.asarray(img, dtype=np.float32)
        
        h, w = arr.shape
        
        # Pad with edge replication to keep output same size
        padded = np.pad(arr, pad_width=1, mode='edge')
        
        # Extract 3x3 sliding windows using stride tricks
        # Shape: (h, w, 3, 3)
        windows = np.lib.stride_tricks.sliding_window_view(padded, (3, 3))
        
        # Explicit convolution: sum over kernel positions
        # Gx and Gy are already flipped appropriately for correlation == convolution
        # when the kernel is symmetric under 180° rotation. Sobel kernels are
        # anti-symmetric, so we need to flip for true convolution:
        gx_mag = np.sum(windows * Gx[::-1, ::-1], axis=(-1, -2))
        gy_mag = np.sum(windows * Gy[::-1, ::-1], axis=(-1, -2))
        
        # Gradient magnitude
        magnitude = np.sqrt(gx_mag**2 + gy_mag**2)
        
        # Clip to [0, 255] and convert to uint8
        magnitude = np.clip(magnitude, 0, 255).astype(np.uint8)
        
        out_path = os.path.join(output_dir, os.path.splitext(fname)[0] + '.png')
        Image.fromarray(magnitude, mode='L').save(out_path)