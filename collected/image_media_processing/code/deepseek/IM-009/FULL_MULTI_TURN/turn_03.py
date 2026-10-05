import numpy as np
from PIL import Image
from pathlib import Path


def _median_from_histogram(histogram):
    """Exact median of integer pixel values from a 256-bin histogram."""
    n = int(histogram.sum())
    if n == 0:
        return float('nan')
    cum = np.cumsum(histogram)
    if n % 2 == 1:
        idx = int(np.searchsorted(cum, (n + 1) // 2, side='left'))
        return float(idx)
    lo = int(np.searchsorted(cum, n // 2, side='left'))
    hi = int(np.searchsorted(cum, n // 2 + 1, side='left'))
    return (lo + hi) / 2.0


def compute_statistics(input_dir):
    """
    Compute per-image 256-bin grayscale histograms plus mean, population std
    (ddof=0), and median of pixel intensity.

    Returns:
        dict: {rel_path: {'histogram': np.ndarray (256,),
                          'mean': float,
                          'std': float,
                          'median': float}}
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp',
                        '.tif', '.tiff', '.gif', '.webp'}
    results = {}
    input_path = Path(input_dir)

    if not input_path.is_dir():
        raise NotADirectoryError(f"'{input_dir}' is not a valid directory")

    for file_path in sorted(input_path.rglob('*')):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in image_extensions:
            continue

        try:
            with Image.open(file_path) as img:
                pixels = np.asarray(img.convert('L'), dtype=np.uint8)
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            continue

        flat = pixels.ravel()

        histogram = np.bincount(flat, minlength=256).astype(np.int64)
        mean = float(np.mean(flat, dtype=np.float64))
        std = float(np.std(flat, dtype=np.float64, ddof=0))
        median = _median_from_histogram(histogram)

        rel_path = str(file_path.relative_to(input_path))
        results[rel_path] = {
            'histogram': histogram,
            'mean': mean,
            'std': std,
            'median': median,
        }

    return results