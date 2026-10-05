from pathlib import Path
import cv2
import numpy as np


def compute_statistics(input_dir: str | Path) -> dict[str, dict]:
    """Computes 256-bin grayscale histogram, mean, and population std deviation for images in input_dir.

    Args:
        input_dir: Path or string path to directory containing images.

    Returns:
        Dict mapping image filenames to dictionary with keys:
            - 'histogram': 1D numpy array of shape (256,) containing pixel counts
            - 'mean': Float mean pixel intensity [0, 255]
            - 'std': Float population standard deviation (divide by N, ddof=0)
    """
    input_path = Path(input_dir)
    if not input_path.is_dir():
        raise ValueError(f"Directory not found: {input_dir}")

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    results = {}

    for file_path in input_path.iterdir():
        if file_path.suffix.lower() not in valid_extensions:
            continue

        # Read directly as 8-bit grayscale (0-255)
        img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue  # Skip unreadable or corrupted images

        # Compute 256-bin histogram [0, 256)
        hist = cv2.calcHist([img], [0], None, [256], [0, 256]).flatten()

        # Compute population mean and standard deviation (ddof=0 explicitly divides by N)
        mean_val = float(np.mean(img))
        std_val = float(np.std(img, ddof=0))

        results[file_path.name] = {
            "histogram": hist.astype(np.int64),
            "mean": mean_val,
            "std": std_val,
        }

    return results