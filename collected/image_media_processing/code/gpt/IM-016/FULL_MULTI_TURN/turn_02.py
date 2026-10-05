from pathlib import Path
from PIL import Image
import math


def sobel_edges(input_dir, output_dir):
    """
    Apply explicit Sobel gradient convolution to every image in input_dir.

    Gx uses the horizontal-gradient Sobel kernel and Gy uses the
    vertical-gradient Sobel kernel. The gradient magnitude is clipped
    to [0, 255] and saved as a grayscale PNG.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Gx: horizontal derivative -> strong response at vertical edges
    Gx_kernel = [
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1],
    ]

    # Gy: vertical derivative -> strong response at horizontal edges
    Gy_kernel = [
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1],
    ]

    valid_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

    for path in input_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in valid_extensions:
            continue

        with Image.open(path) as img:
            gray = img.convert("L")
            width, height = gray.size
            pixels = gray.load()

            output = Image.new("L", (width, height))
            out_pixels = output.load()

            # Edge-replication padding.
            # Clamping coordinates also handles 1x1 and 1-pixel-wide/tall images.
            def get_pixel(x, y):
                x = max(0, min(width - 1, x))
                y = max(0, min(height - 1, y))
                return pixels[x, y]

            for y in range(height):
                for x in range(width):
                    gx = 0
                    gy = 0

                    for ky in range(3):
                        for kx in range(3):
                            px = get_pixel(x + kx - 1, y + ky - 1)

                            # Correct kernel assignment
                            gx += px * Gx_kernel[ky][kx]
                            gy += px * Gy_kernel[ky][kx]

                    # Sobel gradient magnitude
                    magnitude = math.sqrt(gx * gx + gy * gy)

                    # Clip to grayscale range
                    magnitude = min(255, max(0, magnitude))

                    out_pixels[x, y] = int(round(magnitude))

            output_path = output_dir / f"{path.stem}.png"
            output.save(output_path, "PNG")