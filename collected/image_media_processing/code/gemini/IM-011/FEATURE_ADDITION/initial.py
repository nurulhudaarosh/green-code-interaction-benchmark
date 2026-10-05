import os
import shutil
from PIL import Image

def organize_by_resolution(input_dir, output_dir):
    """
    Copies images from input_dir into 'small', 'medium', or 'large' 
    subfolders inside output_dir based on max(width, height):
      - small:  <= 640px
      - medium: > 640px and <= 1920px
      - large:  > 1920px
    """
    # Create target subdirectories
    subfolders = ['small', 'medium', 'large']
    for folder in subfolders:
        os.makedirs(os.path.join(output_dir, folder), exist_ok=True)

    # Valid image extensions to check
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(valid_extensions):
            file_path = os.path.join(input_dir, filename)

            try:
                with Image.open(file_path) as img:
                    max_dim = max(img.width, img.height)

                # Determine resolution category
                if max_dim <= 640:
                    category = 'small'
                elif max_dim <= 1920:
                    category = 'medium'
                else:
                    category = 'large'

                # Copy file to appropriate subfolder
                target_path = os.path.join(output_dir, category, filename)
                shutil.copy2(file_path, target_path)

            except Exception as e:
                print(f"Skipping {filename}: Unable to open or process image. ({e})")

# Example Usage:
# organize_by_resolution('/path/to/source', '/path/to/destination')