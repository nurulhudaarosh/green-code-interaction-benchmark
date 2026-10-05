from pathlib import Path
from PIL import Image
import numpy as np


def sobel_edges(input_dir, output_dir):
    """
    Apply explicit Sobel gradient convolution to every image in input_dir.

    Saves the clipped gradient magnitude as grayscale PNG files in output_dir.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sobel kernels
    Gx = np.array([
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ], dtype=np.float32)

    Gy = np.array([
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1]
    ], dtype=np.float32)

    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

    for path in input_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in image_extensions:
            continue

        # Convert to grayscale
        image = Image.open(path).convert("L")
        img = np.asarray(image, dtype=np.float32)

        # Pad image so border pixels can also be processed
        padded = np.pad(img, ((1, 1), (1, 1)), mode="edge")

        # Explicit Sobel convolution
        gx = np.zeros_like(img, dtype=np.float32)
        gy = np.zeros_like(img, dtype=np.float32)

        for i in range(img.shape[0]):
            for j in range(img.shape[1]):
                region = padded[i:i + 3, j:j + 3]
                gx[i, j] = np.sum(region * Gx)
                gy[i, j] = np.sum(region * Gy)

        # Gradient magnitude
        magnitude = np.sqrt(gx ** 2 + gy ** 2)

        # Clip to valid grayscale range
        magnitude = np.clip(magnitude, 0, 255).astype(np.uint8)

        output_path = output_dir / f"{path.stem}_sobel.png"
        Image.fromarray(magnitude, mode="L").save(output_path)