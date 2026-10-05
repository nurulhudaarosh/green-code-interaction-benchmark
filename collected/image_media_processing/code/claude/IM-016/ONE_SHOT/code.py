"""Sobel edge detection with explicit Gx/Gy convolution (NumPy + Pillow only)."""
from pathlib import Path

import numpy as np
from PIL import Image

SOBEL_GX = np.array([[-1, 0, 1],
                     [-2, 0, 2],
                     [-1, 0, 1]], dtype=np.float64)
SOBEL_GY = np.array([[-1, -2, -1],
                     [0, 0, 0],
                     [1, 2, 1]], dtype=np.float64)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".gif", ".webp"}


def convolve2d(image, kernel):
    """Explicit 2D convolution (kernel flipped), same-size output, edge-replicated borders."""
    kh, kw = kernel.shape
    ph, pw = kh // 2, kw // 2
    padded = np.pad(image, ((ph, ph), (pw, pw)), mode="edge")
    flipped = kernel[::-1, ::-1]
    h, w = image.shape
    out = np.zeros((h, w), dtype=np.float64)
    for i in range(kh):
        for j in range(kw):
            out += flipped[i, j] * padded[i:i + h, j:j + w]
    return out


def sobel_edges(input_dir, output_dir):
    """Compute Sobel gradient magnitude for every image in input_dir.

    Each image is converted to grayscale, convolved with the Sobel Gx and Gy
    kernels, and the magnitude sqrt(Gx^2 + Gy^2) is clipped to [0, 255] and
    saved as an 8-bit grayscale PNG (same file stem) in output_dir.
    Returns the list of written paths.
    """
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue
        with Image.open(path) as img:
            gray = np.asarray(img.convert("L"), dtype=np.float64)

        gx = convolve2d(gray, SOBEL_GX)
        gy = convolve2d(gray, SOBEL_GY)
        magnitude = np.hypot(gx, gy)
        edges = np.clip(magnitude, 0, 255).astype(np.uint8)

        out_path = output_dir / f"{path.stem}.png"
        Image.fromarray(edges, mode="L").save(out_path)
        written.append(out_path)
    return written


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        sys.exit("Usage: python sobel_edges.py <input_dir> <output_dir>")
    for p in sobel_edges(sys.argv[1], sys.argv[2]):
        print(p)