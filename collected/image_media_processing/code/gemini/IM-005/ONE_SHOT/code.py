import os
from PIL import Image, ImageFilter

def apply_blur(input_dir: str, output_dir: str, radius: float) -> None:
    """
    Applies a Gaussian blur of the specified radius to every image in input_dir
    and saves the results to output_dir.

    - radius < 0: Raises ValueError.
    - radius == 0: Copies/saves images as passthrough without applying blur.
    - radius > 0: Applies GaussianBlur with the given radius.
    """
    if radius < 0:
        raise ValueError("Radius must be non-negative.")

    os.makedirs(output_dir, exist_ok=True)

    # Valid image extensions to filter files
    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        try:
            with Image.open(input_path) as img:
                if radius > 0:
                    blurred_img = img.filter(ImageFilter.GaussianBlur(radius))
                    blurred_img.save(output_path)
                else:
                    # Passthrough: save directly without applying blur
                    img.save(output_path)
        except Exception as e:
            print(f"Skipping {filename}: {e}")