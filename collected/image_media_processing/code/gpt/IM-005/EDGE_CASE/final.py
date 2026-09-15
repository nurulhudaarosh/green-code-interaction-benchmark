from pathlib import Path
from PIL import Image, ImageFilter
import shutil


def apply_blur(input_dir, output_dir, radius):
    if radius < 0:
        raise ValueError("radius must be non-negative")

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for input_path in input_dir.rglob("*"):
        if not input_path.is_file():
            continue

        relative_path = input_path.relative_to(input_dir)
        output_path = output_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(input_path) as img:
                if radius == 0:
                    # Passthrough: preserve the original file unchanged.
                    shutil.copy2(input_path, output_path)

                elif img.size == (1, 1):
                    # A 1x1 image cannot be spatially blurred, so preserve
                    # its single pixel and save it as a valid 1x1 image.
                    pixel = img.getpixel((0, 0))
                    output = Image.new(img.mode, (1, 1), pixel)
                    output.save(output_path)

                else:
                    blurred = img.filter(ImageFilter.GaussianBlur(radius))
                    blurred.save(output_path)

        except (OSError, ValueError):
            # Skip files that are not valid images.
            continue