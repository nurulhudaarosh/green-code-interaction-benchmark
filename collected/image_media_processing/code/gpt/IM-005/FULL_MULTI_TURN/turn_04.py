id="84216"
from pathlib import Path
from shutil import copy2
from PIL import Image, ImageFilter


def apply_blur(input_dir, output_dir, radius, filter_type="gaussian"):
    if radius < 0:
        raise ValueError("radius must be non-negative")

    if filter_type not in {"gaussian", "box"}:
        raise ValueError("filter_type must be 'gaussian' or 'box'")

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_extensions = {
        ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"
    }

    for input_path in input_dir.iterdir():
        if not input_path.is_file() or input_path.suffix.lower() not in image_extensions:
            continue

        output_path = output_dir / input_path.name

        # Radius 0: exact byte-for-byte passthrough.
        if radius == 0:
            copy2(input_path, output_path)
            continue

        with Image.open(input_path) as img:
            # A 1x1 image is already uniformly represented by one pixel.
            # Preserve it as a valid 1x1 output instead of relying on the
            # blur filter's handling of this edge case.
            if img.size == (1, 1):
                img.copy().save(output_path)
                continue

            if filter_type == "gaussian":
                blurred = img.filter(ImageFilter.GaussianBlur(radius))
            else:  # filter_type == "box"
                blurred = img.filter(ImageFilter.BoxBlur(radius))

            blurred.save(output_path)