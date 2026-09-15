import os
import shutil
from PIL import Image, ImageFilter

def apply_blur(input_dir: str, output_dir: str, radius: float, filter_type: str = 'gaussian') -> None:
    """
    Applies Gaussian or Box blur of the given radius to every image in input_dir and saves to output_dir.
    
    - Negative radius raises a ValueError.
    - Invalid filter_type raises a ValueError.
    - Radius of 0 acts as an exact byte-identical passthrough.
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
                if filter_type_lower == 'gaussian':
                    blur_filter = ImageFilter.GaussianBlur(radius)
                else:
                    blur_filter = ImageFilter.BoxBlur(radius)

                blurred_img = img.filter(blur_filter)
                blurred_img.save(output_path)