import os
import numpy as np
from PIL import Image


# Explicit Sobel kernels.
# Gx: horizontal-gradient kernel (derivative along x / columns).
#     A purely vertical edge (intensity varies left-to-right) gives a strong Gx.
SOBEL_GX = np.array([
    [-1, 0, 1],
    [-2, 0, 2],
    [-1, 0, 1],
], dtype=np.float32)

# Gy: vertical-gradient kernel (derivative along y / rows).
#     A purely horizontal edge (intensity varies top-to-bottom) gives a strong Gy.
SOBEL_GY = np.array([
    [-1, -2, -1],
    [ 0,  0,  0],
    [ 1,  2,  1],
], dtype=np.float32)


def _convolve2d(image, kernel):
    """Valid 2D convolution of a grayscale image with a 3x3 kernel."""
    kh, kw = kernel.shape
    H, W = image.shape
    out_h = H - kh + 1
    out_w = W - kw + 1
    out = np.zeros((out_h, out_w), dtype=np.float32)

    for i in range(kh):
        for j in range(kw):
            k = kernel[i, j]
            if k != 0.0:
                out += k * image[i:i + out_h, j:j + out_w]
    return out


def _pad_to_shape(arr, target_shape):
    """Zero-pad a 2D array symmetrically to match target_shape."""
    th, tw = target_shape
    h, w = arr.shape
    pad_top = (th - h) // 2
    pad_bottom = th - h - pad_top
    pad_left = (tw - w) // 2
    pad_right = tw - w - pad_left
    return np.pad(arr, ((pad_top, pad_bottom), (pad_left, pad_right)), mode='constant')


def sobel_edges(input_dir, output_dir):
    """Apply Sobel edge detection to every image in input_dir and save
    clipped gradient magnitude as grayscale PNGs in output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    valid_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.webp')

    for fname in sorted(os.listdir(input_dir)):
        if not fname.lower().endswith(valid_exts):
            continue

        in_path = os.path.join(input_dir, fname)
        out_name = os.path.splitext(fname)[0] + '.png'
        out_path = os.path.join(output_dir, out_name)

        with Image.open(in_path) as img:
            gray = np.asarray(img.convert('L'), dtype=np.float32)

        # Explicit Sobel convolutions: Gx = d/dx (horizontal), Gy = d/dy (vertical)
        gx = _convolve2d(gray, SOBEL_GX)
        gy = _convolve2d(gray, SOBEL_GY)

        # Gradient magnitude
        mag = np.sqrt(gx * gx + gy * gy)

        # Restore original spatial size (valid conv shrinks by 2)
        mag = _pad_to_shape(mag, gray.shape)

        mag = np.clip(mag, 0, 255).astype(np.uint8)

        Image.fromarray(mag, mode='L').save(out_path, format='PNG')


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: python sobel_edges.py <input_dir> <output_dir>")
        sys.exit(1)
    sobel_edges(sys.argv[1], sys.argv[2])