import os
import shutil
import json
from PIL import Image


def organize_by_resolution(input_dir, output_dir):
    """
    Copy images into small/medium/large folders based on max(width, height)
    and create a manifest.json.

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

    manifest = []

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

                # Inclusive boundaries:
                # < 640       -> small
                # 640-1920    -> medium
                # > 1920      -> large
                if max_dim < 640:
                    bucket = "small"
                elif max_dim <= 1920:
                    bucket = "medium"
                else:
                    bucket = "large"

            destination_dir = os.path.join(output_dir, bucket)

            shutil.copy2(
                input_path,
                os.path.join(destination_dir, filename)
            )

            manifest.append({
                "filename": filename,
                "bucket": bucket
            })

        except (OSError, Image.UnidentifiedImageError) as e:
            print(f"Skipping {filename}: {e}")

    # Write manifest.json
    manifest_path = os.path.join(output_dir, "manifest.json")

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)