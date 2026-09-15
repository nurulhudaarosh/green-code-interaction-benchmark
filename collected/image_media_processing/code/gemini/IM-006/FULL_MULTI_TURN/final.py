import os
from pathlib import Path
from PIL import Image, UnidentifiedImageError

def extract_metadata(input_dir):
    """
    Extracts metadata from all valid images in input_dir.
    Returns a list of dicts sorted by filename. Handles corrupt/zero-byte files safely.
    """
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff'}
    metadata_list = []
    
    dir_path = Path(input_dir)
    if not dir_path.is_dir():
        return []
    
    for file_path in dir_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            file_size = os.path.getsize(file_path)
            
            # Explicit check for zero-byte files
            if file_size == 0:
                metadata_list.append({
                    "filename": file_path.name,
                    "error": True,
                    "file_size_bytes": 0
                })
                continue
            
            try:
                with Image.open(file_path) as img:
                    # Force loading pixel data to detect truncated or corrupted files
                    img.verify()
                
                # Re-open after verify() because verify() invalidates the image instance
                with Image.open(file_path) as img:
                    width, height = img.size
                    img_format = img.format
                    img_mode = img.mode
                
                aspect_ratio = round(width / height, 3) if height > 0 else 0.0
                
                metadata_list.append({
                    "filename": file_path.name,
                    "format": img_format,
                    "mode": img_mode,
                    "width": width,
                    "height": height,
                    "aspect_ratio": aspect_ratio,
                    "file_size_bytes": file_size,
                    "error": False
                })
            except (IOError, SyntaxError, UnidentifiedImageError, Exception):
                # Catches truncated, corrupted, or unreadable files
                metadata_list.append({
                    "filename": file_path.name,
                    "error": True,
                    "file_size_bytes": file_size
                })
    
    return sorted(metadata_list, key=lambda x: x["filename"])