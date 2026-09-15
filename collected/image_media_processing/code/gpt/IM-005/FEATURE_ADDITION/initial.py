from pathlib import Path
from PIL import Image, ImageFilter
import shutil


def apply_blur(input_dir, output_dir, radius):
    if radius < 0:
        raise ValueError("radius must be non-negative")

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}

    for src in input_dir.iterdir():
        if not src.is_file() or src.suffix.lower() not in image_extensions:
            continue

        dst = output_dir / src.name

        if radius == 0:
            # Exact passthrough: do not open/filter/re-save the image.
            shutil.copy2(src, dst)
        else:
            with Image.open(src) as img:
                blurred = img.filter(ImageFilter.GaussianBlur(radius))
                blurred.save(dst)