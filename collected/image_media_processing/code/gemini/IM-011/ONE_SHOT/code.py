import os
import shutil
from PIL import Image

def organize_by_resolution(input_dir, output_dir):
    """
    Copies images from input_dir into subfolders of output_dir based on dimensions:
    - small: max(width, height) < 640
    - medium: 640 <= max(width, height) <= 1920
    - large: max(width, height) > 1920
    """
    # Create target subdirectories if they don't exist
    categories = ['small', 'medium', 'large']
    for cat in categories:
        os.makedirs(os.path.join(output_dir, cat), exist_ok=True)

    # Valid image extensions to check
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff')

    for root, _, files in os.walk(input_dir):
        for filename in files:
            if filename.lower().endswith(valid_extensions):
                src_path = os.path.join(root, filename)
                
                try:
                    with Image.open(src_path) as img:
                        max_dim = max(img.width, img.height)

                    if max_dim < 640:
                        target_subfolder = 'small'
                    elif max_dim <= 1920:
                        target_subfolder = 'medium'
                    else:
                        target_subfolder = 'large'

                    dest_path = os.path.join(output_dir, target_subfolder, filename)
                    
                    # Copy image to destination
                    shutil.copy2(src_path, dest_path)

                except (IOError, SyntaxError):
                    # Skip corrupted or non-image files
                    continue