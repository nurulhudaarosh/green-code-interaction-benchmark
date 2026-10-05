import os
import shutil
from PIL import Image, UnidentifiedImageError

def organize_by_resolution(input_dir, output_dir):
    """
    Copies images from input_dir into 'small', 'medium', or 'large' 
    subfolders inside output_dir based on their maximum dimension:
    - small:  max(width, height) < 640
    - medium: 640 <= max(width, height) <= 1920  (inclusive of 1920)
    - large:  max(width, height) > 1920
    """
    categories = ['small', 'medium', 'large']
    
    # Ensure destination subdirectories exist
    for category in categories:
        os.makedirs(os.path.join(output_dir, category), exist_ok=True)

    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff')

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        src_path = os.path.join(input_dir, filename)

        try:
            with Image.open(src_path) as img:
                max_dim = max(img.width, img.height)

            if max_dim < 640:
                subfolder = 'small'
            elif max_dim <= 1920:  # <= 1920 ensures exact 1920px falls in medium
                subfolder = 'medium'
            else:
                subfolder = 'large'

            dest_path = os.path.join(output_dir, subfolder, filename)
            shutil.copy2(src_path, dest_path)

        except (UnidentifiedImageError, OSError):
            # Skip invalid or corrupted image files
            continue