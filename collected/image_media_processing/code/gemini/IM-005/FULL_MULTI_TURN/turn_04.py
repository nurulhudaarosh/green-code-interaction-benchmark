import os
import shutil
from PIL import Image, ImageFilter

def apply_blur(input_dir: str, output_dir: str, radius: float, filter_type: str = 'gaussian') -> None:
    """
    Applies Gaussian or Box blur of the given radius to every image in input_dir and saves to output_dir.
    
    - Negative radius raises a ValueError.
    - Invalid filter_type raises a ValueError.
    - Radius of 0 acts as an exact byte-identical passthrough.
    - Handles small images (e.g. 1x1 pixels) and indexed color modes (P, 1) cleanly.
    """
    if radius < 0:
        raise ValueError("Radius must be non-negative (>= 0).")

    filter_type_lower = filter_type.lower()
    if filter_type_lower not in ('gaussian', 'box'):
        raise ValueError(f"Unsupported filter_type '{filter_type}'. Must be 'gaussian' or 'box'.")

    os.makedirs(output_dir, exist_ok=True)

    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        if radius == 0:
            shutil.copy2(input_path, output_path)
        else:
            with Image.open(input_path) as img:
                original_mode = img.mode

                # Convert palette/1-bit modes to RGB/RGBA as Pillow filters require true-color/grayscale modes
                if original_mode in ('1', 'P'):
                    target_img = img.convert('RGBA' if 'transparency' in img.info else 'RGB')
                else:
                    target_img = img

                # Instantiate requested blur filter
                if filter_type_lower == 'gaussian':
                    blur_filter = ImageFilter.GaussianBlur(radius)
                else:
                    blur_filter = ImageFilter.BoxBlur(radius)

                blurred_img = target_img.filter(blur_filter)

                # Convert back if original image was palette-based
                if original_mode in ('1', 'P'):
                    blurred_img = blurred_img.convert(original_mode)

                blurred_img.save(output_path)