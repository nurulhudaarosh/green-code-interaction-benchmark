import os
from PIL import Image, ImageFilter

def apply_blur(input_dir: str, output_dir: str, radius: float) -> None:
    """
    Applies a Gaussian blur of the given radius to every image in input_dir
    and saves the results to output_dir.
    
    - Negative radius raises a ValueError.
    - Radius of 0 passes images through without blurring.
    """
    if radius < 0:
        raise ValueError(f"Radius must be non-negative, got {radius}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Valid image extensions to filter files
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        try:
            with Image.open(input_path) as img:
                # Apply GaussianBlur only if radius > 0
                if radius > 0:
                    blurred_img = img.filter(ImageFilter.GaussianBlur(radius))
                    blurred_img.save(output_path)
                else:
                    # Passthrough mode: save directly without filtering
                    img.save(output_path)
                    
        except (IOError, SyntaxError) as e:
            print(f"Skipping non-image or unreadable file {filename}: {e}")