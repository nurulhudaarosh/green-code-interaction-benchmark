import json
import os
import shutil
from PIL import Image, UnidentifiedImageError

def organize_by_resolution(input_dir, output_dir):
    """
    Copies images from input_dir into 'small', 'medium', or 'large' 
    subfolders inside output_dir based on their maximum dimension:
    - small:  max(width, height) < 640
    - medium: 640 <= max(width, height) <= 1920  (inclusive of 640 and 1920)
    - large:  max(width, height) > 1920

    Generates a 'manifest.json' file in output_dir summarizing assignments.
    """
    categories = ['small', 'medium', 'large']
    
    # Ensure destination subdirectories exist
    for category in categories:
        os.makedirs(os.path.join(output_dir, category), exist_ok=True)

    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff')
    manifest = []

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        src_path = os.path.join(input_dir, filename)

        try:
            with Image.open(src_path) as img:
                max_dim = max(img.width, img.height)

            # Boundary evaluation:
            # - max_dim = 639 -> small (< 640)
            # - max_dim = 640 -> medium (640 <= max_dim <= 1920)
            # - max_dim = 1920 -> medium (640 <= max_dim <= 1920)
            # - max_dim = 1921 -> large (> 1920)
            if max_dim < 640:
                subfolder = 'small'
            elif max_dim <= 1920:
                subfolder = 'medium'
            else:
                subfolder = 'large'

            dest_path = os.path.join(output_dir, subfolder, filename)
            shutil.copy2(src_path, dest_path)

            manifest.append({
                "filename": filename,
                "bucket": subfolder,
                "max_dimension": max_dim
            })

        except (UnidentifiedImageError, OSError):
            # Skip invalid or corrupted image files
            continue

    manifest_path = os.path.join(output_dir, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)