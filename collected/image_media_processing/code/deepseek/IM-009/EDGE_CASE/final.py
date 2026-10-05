import numpy as np
from pathlib import Path
from PIL import Image


def compute_statistics(input_dir):
    """
    Compute per-image 256-bin grayscale histograms plus mean and standard
    deviation of pixel intensity for all images in a directory.

    Args:
        input_dir (str | Path): Directory containing image files.

    Returns:
        dict: {filename: {'histogram': np.ndarray(256,), 'mean': float, 'std': float}}
    """
    supported_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.gif', '.webp'}
    input_dir = Path(input_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    results = {}

    for file_path in sorted(input_dir.iterdir()):
        if not file_path.is_file() or file_path.suffix.lower() not in supported_exts:
            continue

        try:
            with Image.open(file_path) as img:
                gray = np.asarray(img.convert('L'), dtype=np.uint8)
        except Exception as e:
            print(f"Skipping {file_path.name}: {e}")
            continue

        # Flatten to guarantee 1-D even for 1x1 images (shape (1,1) -> (1,))
        pixels = gray.reshape(-1)

        histogram = np.bincount(pixels, minlength=256).astype(np.int64)

        # For a 1x1 image: sum == 1, mean == pixel value, std == 0.0
        # Cast to float64 explicitly so single-pixel std returns 0.0 (not nan)
        values = pixels.astype(np.float64)
        mean = float(values.mean())
        std = float(values.std())  # ddof=0 -> 0.0 for a single sample

        results[file_path.name] = {
            'histogram': histogram,
            'mean': mean,
            'std': std,
        }

    return results