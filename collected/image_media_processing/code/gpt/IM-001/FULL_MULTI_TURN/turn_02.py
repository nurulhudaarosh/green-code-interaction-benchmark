from pathlib import Path
from PIL import Image

def batch_resize(input_dir, output_dir, target_size):
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
                # Create the resized copy
                resized_img = img.resize(target_size)

                # Save the resized image, not the original
                output_file = output_path / image_path.name
                resized_img.save(output_file)

            processed_count += 1

        except (OSError, ValueError):
            continue

    return processed_count