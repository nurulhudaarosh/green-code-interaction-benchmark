import os
from PIL import Image

def extract_metadata(input_dir):
    """
    Extract metadata from all images in input_dir.
    
    Returns a sorted list of dicts with keys:
        filename, format, mode, width, height, file_size_bytes
    """
    results = []
    
    for filename in os.listdir(input_dir):
        filepath = os.path.join(input_dir, filename)
        
        if not os.path.isfile(filepath):
            continue
        
        try:
            with Image.open(filepath) as img:
                results.append({
                    "filename": filename,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "file_size_bytes": os.path.getsize(filepath),
                })
        except (IOError, OSError):
            # Skip files that aren't valid images
            continue
    
    results.sort(key=lambda d: d["filename"])
    return results