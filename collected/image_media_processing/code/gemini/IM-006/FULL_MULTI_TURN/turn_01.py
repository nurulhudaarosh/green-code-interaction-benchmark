import os
from pathlib import Path
from PIL import Image

def extract_metadata(input_dir):
    """
    Extracts metadata from all valid images in input_dir.
    Returns a list of dicts sorted by filename.
    """
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff'}
    metadata_list = []
    
    dir_path = Path(input_dir)
    if not dir_path.is_dir():
        return []
    
    for file_path in dir_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    img_format = img.format
                    img_mode = img.mode
                
                metadata_list.append({
                    "filename": file_path.name,
                    "format": img_format,
                    "mode": img_mode,
                    "width": width,
                    "height": height,
                    "file_size_bytes": file_path.stat().st_size
                })
            except (IOError, SyntaxError):
                # Skip invalid or corrupted image files
                continue
    
    return sorted(metadata_list, key=lambda x: x["filename"])