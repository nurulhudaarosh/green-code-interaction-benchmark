import os
from pathlib import Path
from PIL import Image

def batch_resize(input_dir, output_dir, target_size):
    """
    Resize every PNG/JPEG image in input_dir to target_size and save to output_dir.

    Args:
        input_dir (str): Path to directory containing source images.
        output_dir (str): Path to directory where resized images will be saved.
        target_size (tuple): (width, height) to resize images to.

    Returns:
        int: Number of images successfully processed.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    valid_extensions = {".png", ".jpg", ".jpeg"}
    processed_count = 0

    for file in input_path.iterdir():
        if file.is_file() and file.suffix.lower() in valid_extensions:
            try:
                with Image.open(file) as img:
                    resized_img = img.resize(target_size, Image.LANCZOS)

                    # Preserve original format; convert mode if needed for JPEG
                    save_format = img.format
                    if save_format == "JPEG" and resized_img.mode in ("RGBA", "P"):
                        resized_img = resized_img.convert("RGB")

                    dest_file = output_path / file.name
                    resized_img.save(dest_file, format=save_format)
                    processed_count += 1
            except Exception as e:
                print(f"Skipping {file.name}: {e}")

    return processed_count