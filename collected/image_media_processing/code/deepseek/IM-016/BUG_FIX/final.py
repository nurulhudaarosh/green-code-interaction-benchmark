import numpy as np
from pathlib import Path
from PIL import Image


# --- Sobel kernels ---------------------------------------------------------
# Convention: x increases to the RIGHT, y increases DOWNWARD (image coords).
#
# Gx = horizontal gradient (∂I/∂x): detects VERTICAL edges.
#     A vertical edge (left dark, right bright) yields a large positive Gx.
KERNEL_GX = np.array([
    [-1,  0, +1],
    [-2,  0, +2],
    [-1,  0, +1],
], dtype=np.float32)

# Gy = vertical gradient (∂I/∂y): detects HORIZONTAL edges.
#     A horizontal edge (top dark, bottom bright) yields a large positive Gy.
KERNEL_GY = np.array([
    [-1, -2, -1],
    [ 0,  0,  0],
    [+1, +2, +1],
], dtype=np.float32)


def _convolve2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Explicit 2D 'valid' convolution of a grayscale image with a 3x3 kernel.

    Border pixels (where the kernel doesn't fully overlap) are set to 0,
    so the output has the same shape as the input.
    """
    kh, kw = kernel.shape
    h, w = image.shape
    out_h, out_w = h - kh + 1, w - kw + 1

    windows = np.lib.stride_tricks.sliding_window_view(image, (kh, kw))
    result = np.einsum('ijkl,kl->ij', windows, kernel)

    padded = np.zeros((h, w), dtype=np.float32)
    padded[:out_h, :out_w] = result
    return padded


def _to_grayscale(img: Image.Image) -> np.ndarray:
    if img.mode != 'L':
        img = img.convert('L')
    return np.asarray(img, dtype=np.float32)


def sobel_edges(input_dir: str, output_dir: str) -> None:
    """Apply Sobel edge detection to every image in `input_dir`.

    For each image:
      1. Convert to grayscale.
      2. Convolve with the horizontal-gradient kernel -> Gx,
         and the vertical-gradient kernel -> Gy.
      3. magnitude = sqrt(Gx^2 + Gy^2), clipped to [0, 255].
      4. Save as an 8-bit grayscale PNG in `output_dir`.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")
    output_path.mkdir(parents=True, exist_ok=True)

    valid_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.webp'}

    for entry in sorted(input_path.iterdir()):
        if not entry.is_file() or entry.suffix.lower() not in valid_exts:
            continue

        try:
            with Image.open(entry) as img:
                gray = _to_grayscale(img)
        except Exception as e:
            print(f"Skipping {entry.name}: {e}")
            continue

        # CORRECT assignment:
        #   Gx <- horizontal-gradient kernel (responds to vertical edges)
        #   Gy <- vertical-gradient kernel   (responds to horizontal edges)
        gx = _convolve2d(gray, KERNEL_GX)
        gy = _convolve2d(gray, KERNEL_GY)

        magnitude = np.sqrt(gx * gx + gy * gy)
        magnitude = np.clip(magnitude, 0, 255).astype(np.uint8)

        out_file = output_path / f"{entry.stem}.png"
        Image.fromarray(magnitude, mode='L').save(out_file, format='PNG')
        print(f"{entry.name} -> {out_file.name}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: python sobel.py <input_dir> <output_dir>")
        sys.exit(1)
    sobel_edges(sys.argv[1], sys.argv[2])