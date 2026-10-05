import os
from PIL import Image, ImageOps


def rotate_and_crop(input_dir, output_dir, angle_degrees, crop_size):
    """Rotates images in input_dir and center-crops/pads them to crop_size.

    Args:
        input_dir (str or Path): Path to directory containing source images.
        output_dir (str or Path): Path where output images will be saved.
        angle_degrees (float): Rotation angle in degrees (counter-clockwise).
        crop_size (tuple): Target dimensions as (width, height).
    """
    os.makedirs(output_dir, exist_ok=True)
    target_width, target_height = crop_size
    valid_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        with Image.open(input_path) as img:
            # Preserve alpha channel for RGBA images, otherwise work in RGB
            img = img.convert("RGBA") if img.mode == "RGBA" else img.convert("RGB")

            # 1. Rotate the image (expand=True ensures full canvas is kept)
            rotated = img.rotate(angle_degrees, expand=True, resample=Image.BICUBIC)

            rot_w, rot_h = rotated.size

            # 2. Calculate crop box centered on the rotated image
            left = (rot_w - target_width) / 2
            top = (rot_h - target_height) / 2
            right = left + target_width
            bottom = top + target_height

            # 3. Perform crop (if crop box exceeds image boundaries, PIL pads with transparent/black)
            cropped = rotated.crop((left, top, right, bottom))

            # 4. Enforce exact crop_size with padding if the rotated image was smaller than target
            if cropped.size != crop_size:
                pad_width = max(0, target_width - cropped.width)
                pad_height = max(0, target_height - cropped.height)

                padding = (
                    pad_width // 2,  # left
                    pad_height // 2,  # top
                    pad_width - (pad_width // 2),  # right
                    pad_height - (pad_height // 2),  # bottom
                )
                fill_color = (0, 0, 0, 0) if cropped.mode == "RGBA" else (0, 0, 0)
                cropped = ImageOps.expand(cropped, border=padding, fill=fill_color)

            # 5. Save image
            if filename.lower().endswith((".jpg", ".jpeg")) and cropped.mode == "RGBA":
                cropped = cropped.convert("RGB")

            cropped.save(output_path)


# Example usage:
# rotate_and_crop("input_images", "output_images", angle_degrees=45, crop_size=(256, 256))