import os
import shutil
from PIL import Image

def organize_by_resolution(input_dir, output_dir):
    """
    Copies images from input_dir into subfolders of output_dir 
    based on the maximum dimension (max(width, height)):
    - small:  <= 640px
    - medium: 641px - 1920px
    - large:  > 1920px
    """
    # Define target subdirectories
    categories = ['small', 'medium', 'large']
    for category in categories:
        os.makedirs(os.path.join(output_dir, category), exist_ok=True)
        
    # Valid image extensions
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.gif'}
    
    for filename in os.listdir(input_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue
            
        file_path = os.path.join(input_dir, filename)
        
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                max_dim = max(width, height)
                
                # Determine category
                if max_dim <= 640:
                    category = 'small'
                elif max_dim <= 1920:
                    category = 'medium'
                else:
                    category = 'large'
                
                # Copy file to appropriate subfolder
                target_path = os.path.join(output_dir, category, filename)
                shutil.copy2(file_path, target_path)
                
        except (UnidentifiedImageError, OSError):
            # Skip corrupted or non-image files that pass extension check
            continue