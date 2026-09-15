import os
from PIL import Image, ImageFilter

def apply_blur(input_dir, output_dir, radius):
    if radius < 0:
        raise ValueError(f"radius must be non-negative, got {radius}")

    os.makedirs(output_dir, exist_ok=True)

    valid_ext = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}

    for name in os.listdir(input_dir):
        src_path = os.path.join(input_dir, name)

        if not os.path.isfile(src_path):
            continue
        if os.path.splitext(name)[1].lower() not in valid_ext:
            continue

        with Image.open(src_path) as img:
            if radius == 0:
                # Passthrough: just save a copy, no blurring
                result = img.copy()
            else:
                result = img.filter(ImageFilter.GaussianBlur(radius=radius))

            dst_path = os.path.join(output_dir, name)
            result.save(dst_path)