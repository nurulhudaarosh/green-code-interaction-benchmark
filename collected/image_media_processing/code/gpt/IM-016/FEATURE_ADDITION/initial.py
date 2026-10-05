from pathlib import Path
from PIL import Image
import numpy as np


def sobel_edges(input_dir, output_dir):
    """
    Apply explicit Sobel gradient convolution to every image in input_dir.

    Saves the clipped gradient magnitude as grayscale PNG files
    in output_dir.

    Returns:
        list[str]: Paths of the generated PNG files.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sobel kernels:
    # Gx detects vertical edges (horizontal intensity changes).
    # Gy detects horizontal edges (vertical intensity changes).
    Gx_kernel = np.array([
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ], dtype=np.float32)

    Gy_kernel = np.array([
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1]
    ], dtype=np.float32)

    output_paths = []

    for path in sorted(input_dir.iterdir()):
        if not path.is_file():
            continue

        try:
            with Image.open(path) as img:
                gray = np.asarray(img.convert("L"), dtype=np.float32)
        except (OSError, ValueError):
            continue

        # Pad so the output has the same dimensions as the input.
        padded = np.pad(gray, ((1, 1), (1, 1)), mode="edge")

        # Explicit 3x3 convolution.
        Gx = np.zeros_like(gray, dtype=np.float32)
        Gy = np.zeros_like(gray, dtype=np.float32)

        for i in range(3):
            for j in range(3):
                region = padded[i:i + gray.shape[0],
                                j:j + gray.shape[1]]
                Gx += Gx_kernel[i, j] * region
                Gy += Gy_kernel[i, j] * region

        # Gradient magnitude.
        magnitude = np.sqrt(Gx ** 2 + Gy ** 2)

        # Clip to valid grayscale range.
        magnitude = np.clip(magnitude, 0, 255).astype(np.uint8)

        output_path = output_dir / f"{path.stem}_sobel.png"
        Image.fromarray(magnitude, mode="L").save(output_path)
        output_paths.append(str(output_path))

    return output_paths