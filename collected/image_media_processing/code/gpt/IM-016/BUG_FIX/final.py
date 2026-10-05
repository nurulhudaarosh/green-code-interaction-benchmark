from pathlib import Path
from PIL import Image
import numpy as np


def sobel_edges(input_dir, output_dir):
    """
    Apply explicit Sobel gradient convolution to every image in input_dir.

    Gx measures the horizontal intensity gradient.
    Gy measures the vertical intensity gradient.

    The gradient magnitude is clipped to [0, 255] and saved as
    an 8-bit grayscale PNG.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Horizontal gradient kernel: detects vertical edges
    Gx = np.array([
        [-1,  0,  1],
        [-2,  0,  2],
        [-1,  0,  1]
    ], dtype=np.float32)

    # Vertical gradient kernel: detects horizontal edges
    Gy = np.array([
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1]
    ], dtype=np.float32)

    image_extensions = {
        ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"
    }

    for path in input_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in image_extensions:
            continue

        # Convert input to grayscale
        image = Image.open(path).convert("L")
        img = np.asarray(image, dtype=np.float32)

        # Edge padding for border pixels
        padded = np.pad(img, ((1, 1), (1, 1)), mode="edge")

        gx = np.zeros_like(img, dtype=np.float32)
        gy = np.zeros_like(img, dtype=np.float32)

        # Explicit convolution
        for i in range(img.shape[0]):
            for j in range(img.shape[1]):
                region = padded[i:i + 3, j:j + 3]

                # Gx = horizontal intensity gradient
                gx[i, j] = np.sum(region * Gx)

                # Gy = vertical intensity gradient
                gy[i, j] = np.sum(region * Gy)

        # Sobel gradient magnitude
        magnitude = np.sqrt(gx ** 2 + gy ** 2)

        # Clip to 8-bit grayscale range
        magnitude = np.clip(magnitude, 0, 255).astype(np.uint8)

        output_path = output_dir / f"{path.stem}_sobel.png"
        Image.fromarray(magnitude, mode="L").save(output_path)