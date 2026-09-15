import os
from PIL import Image, ImageFilter, UnidentifiedImageError


def apply_blur(input_dir, output_dir, radius, filter_type="gaussian"):
    if radius < 0:
        raise ValueError("radius must be non-negative")
    if filter_type not in ("gaussian", "box"):
        raise ValueError("filter_type must be 'gaussian' or 'box'")
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    filter_cls = ImageFilter.GaussianBlur if filter_type == "gaussian" else ImageFilter.BoxBlur

    for filename in os.listdir(input_dir):
        src_path = os.path.join(input_dir, filename)
        if not os.path.isfile(src_path):
            continue

        try:
            with Image.open(src_path) as img:
                if radius == 0:
                    img.save(os.path.join(output_dir, filename))
                else:
                    img.filter(filter_cls(radius=radius)).save(
                        os.path.join(output_dir, filename)
                    )
        except UnidentifiedImageError:
            continue