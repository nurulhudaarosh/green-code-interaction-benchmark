from pathlib import Path
from PIL import Image
import math


def sobel_edges(input_dir, output_dir, threshold=None):
    """
    Apply explicit Sobel gradient convolution to every image in input_dir.

    Parameters:
        input_dir: Directory containing input images.
        output_dir: Directory for output PNG files.
        threshold: Optional binary threshold. If provided:
                   magnitude > threshold -> 255
                   otherwise -> 0

    Uses edge-replication padding, including for 1-pixel-wide,
    1-pixel-tall, and 1x1 images.
    """

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Gx: horizontal derivative -> detects vertical edges
    Gx_kernel = [
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1],
    ]

    # Gy: vertical derivative -> detects horizontal edges
    Gy_kernel = [
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1],
    ]

    valid_extensions = {
        ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"
    }

    for path in input_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in valid_extensions:
            continue

        with Image.open(path) as img:
            gray = img.convert("L")
            width, height = gray.size
            pixels = gray.load()

            output = Image.new("L", (width, height))
            out_pixels = output.load()

            def get_pixel(x, y):
                """
                Edge-replication padding.

                Coordinates outside the image are replaced by the
                nearest valid coordinate. This handles:
                  - 1x1 images
                  - 1xN images
                  - Nx1 images
                  - normal images
                """
                x = max(0, min(width - 1, x))
                y = max(0, min(height - 1, y))
                return pixels[x, y]

            for y in range(height):
                for x in range(width):
                    gx = 0
                    gy = 0

                    # Explicit 3x3 Sobel convolution
                    for ky in range(3):
                        for kx in range(3):
                            px = get_pixel(
                                x + kx - 1,
                                y + ky - 1
                            )

                            gx += px * Gx_kernel[ky][kx]
                            gy += px * Gy_kernel[ky][kx]

                    magnitude = math.sqrt(
                        gx * gx + gy * gy
                    )

                    if threshold is not None:
                        # Binary output
                        out_pixels[x, y] = (
                            255 if magnitude > threshold else 0
                        )
                    else:
                        # Raw magnitude, clipped to [0, 255]
                        magnitude = min(255, max(0, magnitude))
                        out_pixels[x, y] = int(round(magnitude))

            output_path = output_dir / f"{path.stem}.png"
            output.save(output_path, "PNG")