import os
from pathlib import Path
import cv2
import numpy as np


def sobel_edges(input_dir: str | Path, output_dir: str | Path) -> None:
    """Applies explicit Sobel edge detection to all images in input_dir and saves

    the gradient magnitude as grayscale PNGs in output_dir.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Explicit Sobel Kernels
    # Gx detects vertical edges (horizontal gradient)
    Gx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)

    # Gy detects horizontal edges (vertical gradient)
    Gy = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

    for file_path in input_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            # 1. Read input image as grayscale
            img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            # Convert to float64/float32 to prevent underflow/overflow during convolution
            img_float = img.astype(np.float32)

            # 2. Perform explicit convolution using Gx and Gy kernels
            # cv2.filter2D with borderType=cv2.BORDER_REFLECT handles boundary padding
            grad_x = cv2.filter2D(img_float, ddepth=-1, kernel=Gx)
            grad_y = cv2.filter2D(img_float, ddepth=-1, kernel=Gy)

            # 3. Compute gradient magnitude
            magnitude = np.sqrt(grad_x**2 + grad_y**2)

            # 4. Clip to valid [0, 255] byte range and cast to uint8
            magnitude_clipped = np.clip(magnitude, 0, 255).astype(np.uint8)

            # 5. Save output as grayscale PNG
            output_filename = output_path / f"{file_path.stem}_sobel.png"
            cv2.imwrite(str(output_filename), magnitude_clipped)


if __name__ == "__main__":
    # Example usage
    sobel_edges("input_images", "output_images")