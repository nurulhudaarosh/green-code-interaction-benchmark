import os
import numpy as np
from PIL import Image

# Sobel kernels (standard form: Gx responds to horizontal change, Gy to vertical)
SOBEL_X = np.array([[-1, 0, 1],
                    [-2, 0, 2],
                    [-1, 0, 1]], dtype=np.float32)
SOBEL_Y = np.array([[-1, -2, -1],
                    [ 0,  0,  0],
                    [ 1,  2,  1]], dtype=np.float32)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def _convolve2d(img, kernel):
    """Explicit 2D convolution (kernel flipped), 'same' output, edge-replicated padding."""
    kh, kw = kernel.shape
    ph, pw = kh // 2, kw // 2
    padded = np.pad(img, ((ph, ph), (pw, pw)), mode="edge")
    k = kernel[::-1, ::-1]  # flip for true convolution
    h, w = img.shape
    out = np.zeros((h, w), dtype=np.float32)
    for i in range(kh):
        for j in range(kw):
            out += k[i, j] * padded[i:i + h, j:j + w]
    return out


def sobel_edges(input_dir, output_dir):
    """Compute Sobel gradient magnitude for every image in input_dir.

    Each image is converted to grayscale, convolved with the Sobel Gx and Gy
    kernels, and the magnitude sqrt(Gx^2 + Gy^2) is clipped to [0, 255] and
    saved as an 8-bit grayscale PNG in output_dir (same base filename).
    Returns the list of saved file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    saved = []

    for name in sorted(os.listdir(input_dir)):
        stem, ext = os.path.splitext(name)
        if ext.lower() not in IMAGE_EXTS:
            continue
        src = os.path.join(input_dir, name)
        if not os.path.isfile(src):
            continue

        with Image.open(src) as im:
            gray = np.asarray(im.convert("L"), dtype=np.float32)

        gx = _convolve2d(gray, SOBEL_X)
        gy = _convolve2d(gray, SOBEL_Y)
        mag = np.sqrt(gx ** 2 + gy ** 2)
        mag = np.clip(mag, 0, 255).astype(np.uint8)

        dst = os.path.join(output_dir, stem + ".png")
        Image.fromarray(mag, mode="L").save(dst)
        saved.append(dst)

    return saved


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        sys.exit("usage: python sobel_edges.py <input_dir> <output_dir>")
    for p in sobel_edges(sys.argv[1], sys.argv[2]):
        print("saved", p)