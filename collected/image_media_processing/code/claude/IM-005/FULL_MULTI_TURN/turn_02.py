import os
import shutil
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

        dst_path = os.path.join(output_dir, name)

        if radius == 0:
            # True passthrough: copy raw bytes, never decode/re-encode via Pillow.
            shutil.copyfile(src_path, dst_path)
            continue

        with Image.open(src_path) as img:
            result = img.filter(ImageFilter.GaussianBlur(radius=radius))
            result.save(dst_path)