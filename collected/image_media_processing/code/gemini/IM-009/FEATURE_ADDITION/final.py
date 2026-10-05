import os
import numpy as np

try:
    import cv2

    HAS_OPENCV = True
except ImportError:
    from PIL import Image

    HAS_OPENCV = False


def _median_from_histogram(hist: np.ndarray) -> float:
    """Computes the median intensity directly from a 256-bin histogram."""
    cumulative = np.cumsum(hist)
    total_pixels = cumulative[-1]
    if total_pixels == 0:
        return 0.0

    target = total_pixels / 2.0
    # Find the first bin where the cumulative count meets or exceeds half the total pixels
    median_bin = np.searchsorted(cumulative, target)
    return float(median_bin)


def compute_statistics(input_dir: str) -> dict:
    """Computes grayscale histogram (256 bins), mean, standard deviation, and

    median pixel intensity for each image in the specified directory.

    Args:
        input_dir: Path to the directory containing image files.

    Returns:
        A dictionary mapping image filenames to their statistics:
        {
            "image.jpg": {
                "histogram": np.ndarray (shape: (256,)),
                "mean": float,
                "std": float,
                "median": float
            }
        }
    """
    results = {}
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

    if not os.path.isdir(input_dir):
        raise ValueError(f"Directory not found: {input_dir}")

    for filename in sorted(os.listdir(input_dir)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue

        file_path = os.path.join(input_dir, filename)

        if HAS_OPENCV:
            img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            hist = cv2.calcHist([img], [0], None, [256], [0, 256]).ravel()
            mean_val, std_val = cv2.meanStdDev(img)
            median_val = _median_from_histogram(hist)

            results[filename] = {
                "histogram": hist,
                "mean": float(mean_val[0][0]),
                "std": float(std_val[0][0]),
                "median": median_val,
            }
        else:
            try:
                with Image.open(file_path) as img:
                    img_gray = np.array(img.convert("L"))

                hist, _ = np.histogram(img_gray, bins=256, range=(0, 256))
                median_val = _median_from_histogram(hist)

                results[filename] = {
                    "histogram": hist,
                    "mean": float(np.mean(img_gray)),
                    "std": float(np.std(img_gray)),
                    "median": median_val,
                }
            except Exception:
                continue

    return results