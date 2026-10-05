from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError


def _median_from_histogram(hist):
    """Median intensity from a histogram of counts.

    Matches np.median: for an even pixel count, averages the two middle values.
    """
    cumulative = np.cumsum(hist)
    n = int(cumulative[-1])
    # Bin holding the k-th smallest pixel (0-based rank k) is the first bin
    # whose cumulative count exceeds k.
    lower = np.searchsorted(cumulative, (n - 1) // 2 + 1, side="left")
    upper = np.searchsorted(cumulative, n // 2 + 1, side="left")
    return float((lower + upper) / 2)


def compute_statistics(input_dir):
    """Compute grayscale statistics for every image in a directory.

    Args:
        input_dir: Path to a directory containing image files. Files that
            Pillow cannot open as images are skipped.

    Returns:
        dict mapping each image's filename to a dict with:
            "histogram": np.ndarray of shape (256,), pixel counts per
                         intensity value 0-255
            "mean":      mean pixel intensity (float)
            "median":    median pixel intensity, computed from the histogram
                         (float; averages the two middle values for an even
                         pixel count, like np.median)
            "std":       population standard deviation of intensity (float)
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    results = {}
    for path in sorted(input_dir.iterdir()):
        if not path.is_file():
            continue
        try:
            with Image.open(path) as img:
                gray = np.asarray(img.convert("L"), dtype=np.uint8)
        except (UnidentifiedImageError, OSError):
            continue  # not an image (or unreadable); skip it

        pixels = gray.ravel()
        histogram = np.bincount(pixels, minlength=256)
        results[path.name] = {
            "histogram": histogram,
            "mean": float(pixels.mean()),
            "median": _median_from_histogram(histogram),
            "std": float(pixels.std()),
        }
    return results


if __name__ == "__main__":
    import sys

    for name, s in compute_statistics(sys.argv[1]).items():
        print(f"{name}: mean={s['mean']:.2f} median={s['median']:.1f} std={s['std']:.2f}")