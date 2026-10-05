import os
from pathlib import Path
from typing import Optional
import cv2
import numpy as np


def sobel_edges(
    input_dir: str | Path,
    output_dir: str | Path,
    threshold: Optional[float] = None,
) -> None:
    """Applies explicit Sobel edge detection to all images in input_dir and saves

    the gradient output as grayscale PNGs in output_dir.

    Args:
        input_dir: Path to directory containing source images.
        output_dir: Path to directory where output PNGs will be written.
        threshold: Optional cutoff float. If provided, values > threshold become
          255, otherwise 0. If None, saves clipped continuous gradient magnitude
          [0, 255].
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Explicit Sobel Derivative Kernels
    # Gx: Derivative w.r.t. x (detects vertical lines / horizontal intensity transitions)
    Gx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)

    # Gy: Derivative w.r.t. y (detects horizontal lines / vertical intensity transitions)
    Gy = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

    for file_path in input_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            img_float = img.astype(np.float32)

            # 1. Spatial correlation using explicit kernels
            grad_x = cv2.filter2D(img_float, ddepth=cv2.CV_32F, kernel=Gx)
            grad_y = cv2.filter2D(img_float, ddepth=cv2.CV_32F, kernel=Gy)

            # 2. Gradient magnitude
            magnitude = np.sqrt(grad_x**2 + grad_y**2)

            # 3. Apply thresholding if threshold is specified, else continuous clip
            if threshold is not None:
                output_map = np.where(magnitude > threshold, 255, 0).astype(
                    np.uint8
                )
            else:
                output_map = np.clip(magnitude, 0, 255).astype(np.uint8)

            # 4. Save result
            output_filename = output_path / f"{file_path.stem}_sobel.png"
            cv2.imwrite(str(output_filename), output_map)


if __name__ == "__main__":
    # Example 1: Continuous gradient magnitude map
    sobel_edges("input_images", "output_continuous")

    # Example 2: Binary edge map with threshold = 100.0
    sobel_edges("input_images", "output_binary", threshold=100.0)