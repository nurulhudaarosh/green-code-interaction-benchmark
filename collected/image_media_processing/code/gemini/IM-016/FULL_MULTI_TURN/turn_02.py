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

    # Explicit Sobel Cross-Correlation / Derivative Kernels
    #
    # Gx computes partial derivative w.r.t. x (columns): dI / dx
    # A step change from dark on left to bright on right gives positive response.
    Gx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)

    # Gy computes partial derivative w.r.t. y (rows): dI / dy
    # A step change from dark on top to bright on bottom gives positive response.
    Gy = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

    for file_path in input_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            img_float = img.astype(np.float32)

            # Use cv2.filter2D with anchor=(-1,-1)
            # Use cv2.BORDER_REFLECT_101 for standard mirror padding
            # Note: cv2.filter2D calculates cross-correlation. To strictly enforce 
            # spatial correlation matching the partial derivatives dI/dx and dI/dy:
            grad_x = cv2.filter2D(img_float, ddepth=cv2.CV_32F, kernel=Gx)
            grad_y = cv2.filter2D(img_float, ddepth=cv2.CV_32F, kernel=Gy)

            # Gradient Magnitude: sqrt(Gx^2 + Gy^2)
            magnitude = np.sqrt(grad_x**2 + grad_y**2)

            # Clip magnitude to [0, 255] and cast to uint8
            magnitude_clipped = np.clip(magnitude, 0, 255).astype(np.uint8)

            output_filename = output_path / f"{file_path.stem}_sobel.png"
            cv2.imwrite(str(output_filename), magnitude_clipped)


if __name__ == "__main__":
    # Synthetic verification test for Gx (vertical edge):
    synthetic_img = np.zeros((10, 10), dtype=np.float32)
    synthetic_img[:, 5:] = 255.0  # Vertical step edge at x=5

    Gx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    Gy = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

    gx_response = cv2.filter2D(synthetic_img, ddepth=-1, kernel=Gx)
    gy_response = cv2.filter2D(synthetic_img, ddepth=-1, kernel=Gy)

    print(
        f"Synthetic Vertical Edge -> Max Gx: {np.max(np.abs(gx_response))}, Max Gy: {np.max(np.abs(gy_response))}"
    )
    # Output: Synthetic Vertical Edge -> Max Gx: 1020.0, Max Gy: 0.0