import os

import numpy as np
from PIL import Image

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".gif", ".webp"}

# Sobel kernels (correlation form)
KX = np.array([[-1, 0, 1],
               [-2, 0, 2],
               [-1, 0, 1]], dtype=np.float64)
KY = np.array([[-1, -2, -1],
               [0, 0, 0],
               [1, 2, 1]], dtype=np.float64)


def convolve2d(image, kernel):
    """Explicit 2D convolution (kernel flipped) with edge-replicated padding.

    Output has the same shape as `image`.
    """
    kh, kw = kernel.shape
    ph, pw = kh // 2, kw // 2
    flipped = kernel[::-1, ::-1]  # true convolution flips both axes
    h, w = image.shape
    if h == 0 or w == 0:
        raise ValueError("Cannot convolve an empty image")
    # mode="edge" replicates the border pixel, which is well defined even when
    # an axis has length 1 (so 1xN, Nx1 and 1x1 images need no special case).
    # The padded array is always (h + 2*ph) x (w + 2*pw), so every slice below
    # stays in bounds.
    padded = np.pad(image, ((ph, ph), (pw, pw)), mode="edge")
    out = np.zeros((h, w), dtype=np.float64)
    for i in range(kh):
        for j in range(kw):
            out += flipped[i, j] * padded[i:i + h, j:j + w]
    return out


def sobel_edges(input_dir, output_dir):
    """Compute Sobel gradient magnitude for every image in input_dir.

    Each image is converted to grayscale, convolved with the Sobel Gx and Gy
    kernels, and the magnitude sqrt(Gx^2 + Gy^2) is clipped to [0, 255] and
    saved as an 8-bit grayscale PNG in output_dir (same base name).

    Returns the list of written file paths.
    """
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"Input directory not found: {input_dir}")
    os.makedirs(output_dir, exist_ok=True)

    written = []
    for name in sorted(os.listdir(input_dir)):
        stem, ext = os.path.splitext(name)
        if ext.lower() not in IMAGE_EXTS:
            continue
        src = os.path.join(input_dir, name)
        if not os.path.isfile(src):
            continue

        with Image.open(src) as img:
            gray = np.asarray(img.convert("L"), dtype=np.float64)

        gx = convolve2d(gray, KX)
        gy = convolve2d(gray, KY)
        magnitude = np.sqrt(gx ** 2 + gy ** 2)
        result = np.clip(magnitude, 0, 255).astype(np.uint8)

        dst = os.path.join(output_dir, stem + ".png")
        Image.fromarray(result, mode="L").save(dst)
        written.append(dst)

    return written


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python sobel_edges.py <input_dir> <output_dir>")
        sys.exit(1)
    for path in sobel_edges(sys.argv[1], sys.argv[2]):
        print("Saved", path)