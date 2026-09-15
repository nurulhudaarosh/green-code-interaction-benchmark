from pathlib import Path
from PIL import Image

def batch_resize(input_dir, output_dir, target_size):
    """
    Resize every PNG/JPEG image in input_dir to target_size.

    Args:
        input_dir: Directory containing input images.
        output_dir: Directory where resized images will be saved.
        target_size: Tuple (width, height).

    Returns:
        int: Number of successfully processed images.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_extensions = {".png", ".jpg", ".jpeg"}
    count = 0

    for image_path in input_dir.iterdir():
        if image_path.is_file() and image_path.suffix.lower() in valid_extensions:
            try:
                with Image.open(image_path) as img:
                    resized = img.resize(target_size)
                    output_path = output_dir / image_path.name
                    resized.save(output_path)

                count += 1

            except (OSError, ValueError) as e:
                print(f"Skipping {image_path.name}: {e}")

    return count