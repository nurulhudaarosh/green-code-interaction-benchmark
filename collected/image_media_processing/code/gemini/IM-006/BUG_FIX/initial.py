import os
from PIL import Image

def extract_metadata(input_dir):
    metadata_list = []
    
    # Supported PIL extensions
    supported_extensions = Image.registered_extensions()
    
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        
        # Process regular files with standard image extensions
        if os.path.isfile(file_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in supported_extensions:
                try:
                    with Image.open(file_path) as img:
                        file_size = os.path.getsize(file_path)
                        width, height = img.size
                        
                        metadata_list.append({
                            "filename": filename,
                            "format": img.format,
                            "mode": img.mode,
                            "width": width,
                            "height": height,
                            "file_size_bytes": file_size
                        })
                except (IOError, SyntaxError):
                    # Skip non-image files or corrupt images
                    continue

    # Sort list alphabetically by filename
    return sorted(metadata_list, key=lambda x: x["filename"])