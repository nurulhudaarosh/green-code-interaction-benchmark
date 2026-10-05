from pathlib import Path
import numpy as np
from PIL import Image
from scipy.signal import convolve2d


def sobel_edges(input_dir: str | Path, output_dir: str | Path) -> None:
    """Applies explicit Sobel gradient convolution to all PNG and JPG images in

    input_dir and saves the clipped gradient magnitude to output_dir.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 3x3 Sobel kernels
    Gx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)

    Gy = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

    # Supported image extensions
    valid_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}

    for file_path in input_path.iterdir():
        if file_path.suffix.lower() not in valid_extensions:
            continue

        # Load image and convert to grayscale float32 array in [0, 255]
        img = Image.open(file_path).convert("L")
        img_arr = np.asarray(img, dtype=np.float32)

        # Explicit 2D spatial convolution
        grad_x = convolve2d(img_arr, Gx, mode="same", boundary="symm")
        grad_y = convolve2d(img_arr, Gy, mode="same", boundary="symm")

        # Compute gradient magnitude
        magnitude = np.hypot(grad_x, grad_y)

        # Clip values to valid [0, 255] range and convert to uint8
        magnitude_clipped = np.clip(magnitude, 0, 255).astype(np.uint8)

        # Save result as grayscale PNG
        out_img = Image.fromarray(magnitude_clipped)
        out_file = output_path / f"{file_path.stem}_sobel.png"
        out_img.save(out_file)


if __name__ == "__main__":
    sobel_edges("input_images", "output_edges")