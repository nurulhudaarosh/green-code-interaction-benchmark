import os
import shutil
from PIL import Image, ImageFilter

def apply_blur(input_dir: str, output_dir: str, radius: float) -> None:
    """
    Applies Gaussian blur of the given radius to every image in input_dir and saves to output_dir.
    - Negative radius raises a ValueError.
    - Radius of 0 acts as a exact byte-identical passthrough.
    """
    if radius < 0:
        raise ValueError("Radius must be non-negative (>= 0).")

    os.makedirs(output_dir, exist_ok=True)

    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        if radius == 0:
            # Direct binary copy to ensure byte-identical output without re-encoding
            shutil.copy2(input_path, output_path)
        else:
            with Image.open(input_path) as img:
                blurred_img = img.filter(ImageFilter.GaussianBlur(radius))
                blurred_img.save(output_path)