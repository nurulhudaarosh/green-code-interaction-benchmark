import os
import shutil
from PIL import Image


def organize_by_resolution(input_dir, output_dir):
    """
    Copy images into small/medium/large folders based on max(width, height).

    small:  max_dim < 640
    medium: 640 <= max_dim <= 1920
    large:  max_dim > 1920
    """

    small_dir = os.path.join(output_dir, "small")
    medium_dir = os.path.join(output_dir, "medium")
    large_dir = os.path.join(output_dir, "large")

    os.makedirs(small_dir, exist_ok=True)
    os.makedirs(medium_dir, exist_ok=True)
    os.makedirs(large_dir, exist_ok=True)

    image_extensions = {
        ".jpg", ".jpeg", ".png", ".bmp",
        ".gif", ".tiff", ".webp"
    }

    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)

        if not os.path.isfile(input_path):
            continue

        if os.path.splitext(filename)[1].lower() not in image_extensions:
            continue

        try:
            with Image.open(input_path) as img:
                width, height = img.size
                max_dim = max(width, height)

                if max_dim < 640:
                    destination_dir = small_dir
                elif max_dim <= 1920:  # Fixed: 1920 is included in medium
                    destination_dir = medium_dir
                else:
                    destination_dir = large_dir

            shutil.copy2(
                input_path,
                os.path.join(destination_dir, filename)
            )

        except (OSError, Image.UnidentifiedImageError) as e:
            print(f"Skipping {filename}: {e}")