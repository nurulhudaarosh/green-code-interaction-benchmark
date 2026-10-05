import os
from pathlib import Path
from PIL import Image
import numpy as np


def rotate_and_crop(input_dir, output_dir, angle_degrees, crop_size):
    """
    Rotate each image in input_dir by angle_degrees and center-crop/pad to crop_size.
    
    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory to save processed images.
        angle_degrees (float): Rotation angle in degrees (counter-clockwise).
        crop_size (tuple): Target size as (width, height).
    
    Returns:
        int: Number of images processed.
    """
    if isinstance(crop_size, int):
        crop_size = (crop_size, crop_size)
    target_w, target_h = crop_size

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}
    processed = 0

    for img_file in sorted(input_path.iterdir()):
        if not img_file.is_file() or img_file.suffix.lower() not in valid_exts:
            continue

        try:
            with Image.open(img_file) as img:
                # Preserve alpha channel if present; otherwise use RGB
                has_alpha = img.mode in ('RGBA', 'LA') or (
                    img.mode == 'P' and 'transparency' in img.info
                )
                work = img.convert('RGBA' if has_alpha else 'RGB')

                # Rotate with expand so nothing is clipped, fill with transparent/black
                fill = (0, 0, 0, 0) if has_alpha else (0, 0, 0)
                rotated = work.rotate(
                    angle_degrees,
                    resample=Image.BICUBIC,
                    expand=True,
                    fillcolor=fill,
                )

                rw, rh = rotated.size
                # Crop box centered on the rotated image
                left = (rw - target_w) // 2
                top = (rh - target_h) // 2

                # If rotated image is smaller than target, pad; else crop
                if target_w <= rw and target_h <= rh:
                    cropped = rotated.crop(
                        (left, top, left + target_w, top + target_h)
                    )
                else:
                    # Compute intersection region and paste into a blank canvas
                    src_left = max(0, left)
                    src_top = max(0, top)
                    src_right = min(rw, left + target_w)
                    src_bottom = min(rh, top + target_h)

                    region = rotated.crop(
                        (src_left, src_top, src_right, src_bottom)
                    )

                    canvas = Image.new(
                        'RGBA' if has_alpha else 'RGB',
                        (target_w, target_h),
                        fill,
                    )
                    paste_x = src_left - left
                    paste_y = src_top - top
                    canvas.paste(region, (paste_x, paste_y))
                    cropped = canvas

                # Save with matching extension (normalize jpeg)
                out_file = output_path / img_file.name
                save_kwargs = {}
                if out_file.suffix.lower() in ('.jpg', '.jpeg'):
                    cropped = cropped.convert('RGB')
                    save_kwargs = {'quality': 95, 'subsampling': 0}
                cropped.save(out_file, **save_kwargs)
                processed += 1

        except Exception as e:
            print(f"Failed to process {img_file}: {e}")

    return processed


if __name__ == "__main__":
    # Example usage
    n = rotate_and_crop(
        input_dir="input_images",
        output_dir="output_images",
        angle_degrees=30,
        crop_size=(256, 256),
    )
    print(f"Processed {n} images.")