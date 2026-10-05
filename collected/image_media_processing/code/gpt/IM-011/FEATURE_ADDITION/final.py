import os
import shutil
import json
from PIL import Image


def organize_by_resolution(input_dir, output_dir):
    """
    Copy images into small, medium, or large subfolders based on
    their maximum dimension, and write a manifest.json file.

    Thresholds:
        small:  max(width, height) <= 640
        medium: 640 < max(width, height) <= 1920
        large:  max(width, height) > 1920
    """

    # Create output subfolders
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

        # Skip directories
        if not os.path.isfile(input_path):
            continue

        # Skip non-image files
        if os.path.splitext(filename)[1].lower() not in image_extensions:
            continue

        try:
            with Image.open(input_path) as img:
                width, height = img.size
                max_dim = max(width, height)

                # Assign bucket
                if max_dim <= 640:
                    bucket = "small"
                    destination_dir = small_dir
                elif max_dim <= 1920:
                    bucket = "medium"
                    destination_dir = medium_dir
                else:
                    bucket = "large"
                    destination_dir = large_dir

            # Copy the image
            shutil.copy2(
                input_path,
                os.path.join(destination_dir, filename)
            )

            # Add entry to manifest
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