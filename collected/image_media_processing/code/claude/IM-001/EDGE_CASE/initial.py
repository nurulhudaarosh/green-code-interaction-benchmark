import os
from pathlib import Path
from PIL import Image

def batch_resize(input_dir, output_dir, target_size):
    """
    Resize every PNG/JPEG image in input_dir to target_size and save to output_dir.

    Args:
        input_dir: path to folder containing source images
        output_dir: path to folder where resized images will be saved
        target_size: (width, height) tuple

    Returns:
        int: number of images successfully processed
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_extensions = {".png", ".jpg", ".jpeg"}
    processed_count = 0

    for file_path in input_dir.iterdir():
        if file_path.suffix.lower() not in valid_extensions:
            continue
        if not file_path.is_file():
            continue

        try:
            with Image.open(file_path) as img:
                # Convert to RGB for JPEGs to avoid mode issues (e.g. RGBA -> JPEG)
                if file_path.suffix.lower() in {".jpg", ".jpeg"} and img.mode != "RGB":
                    img = img.convert("RGB")

                resized = img.resize(target_size, Image.LANCZOS)
                resized.save(output_dir / file_path.name)
                processed_count += 1
        except Exception as e:
            print(f"Skipping {file_path.name}: {e}")

    return processed_count