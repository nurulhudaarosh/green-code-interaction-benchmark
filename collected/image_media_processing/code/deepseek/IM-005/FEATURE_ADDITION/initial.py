import os
from PIL import Image, ImageFilter, UnidentifiedImageError


def apply_blur(input_dir, output_dir, radius):
    if radius < 0:
        raise ValueError("radius must be non-negative")
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        src_path = os.path.join(input_dir, filename)
        if not os.path.isfile(src_path):
            continue

        try:
            with Image.open(src_path) as img:
                if radius == 0:
                    img.save(os.path.join(output_dir, filename))
                else:
                    img.filter(ImageFilter.GaussianBlur(radius=radius)).save(
                        os.path.join(output_dir, filename)
                    )
        except UnidentifiedImageError:
            continue