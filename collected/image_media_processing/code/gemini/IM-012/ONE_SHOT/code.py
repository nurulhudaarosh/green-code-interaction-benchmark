import os
import glob
from PIL import Image, ImageOps


def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """
    Resizes images in `input_dir` preserving aspect ratio and pads them to
    `target_size`, keeping content centered. Saves processed images to `output_dir`.

    :param input_dir: Path to directory containing source images.
    :param output_dir: Path to save processed images.
    :param target_size: Tuple (width, height) specifying target dimensions.
    :param pad_color: RGB tuple specifying padding color (default black).
    """
    os.makedirs(output_dir, exist_ok=True)
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

    for filename in os.listdir(input_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        with Image.open(input_path) as img:
            # Preserve color mode compatibility for padding
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

            # Scale image down/up while maintaining aspect ratio
            img.thumbnail(target_size, Image.Resampling.LANCZOS)

            # Compute padding to center content
            pad_w = target_size[0] - img.width
            pad_h = target_size[1] - img.height

            left = pad_w // 2
            top = pad_h // 2
            right = pad_w - left
            bottom = pad_h - top

            # Apply border/padding
            padded_img = ImageOps.expand(
                img, border=(left, top, right, bottom), fill=pad_color
            )

            padded_img.save(output_path)