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
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    valid_extensions = {".png", ".jpg", ".jpeg"}
    processed_count = 0

    for image_path in input_path.iterdir():
        if not image_path.is_file() or image_path.suffix.lower() not in valid_extensions:
            continue

        try:
            with Image.open(image_path) as img:
                resized = img.resize(target_size)

                output_file = output_path / image_path.name
                resized.save(output_file)

            processed_count += 1

        except (OSError, ValueError):
            # Skip files that cannot be opened or resized
            continue

    return processed_count