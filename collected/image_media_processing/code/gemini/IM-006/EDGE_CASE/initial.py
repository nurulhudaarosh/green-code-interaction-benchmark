from pathlib import Path
from PIL import Image, UnidentifiedImageError

def extract_metadata(input_dir: str) -> list[dict]:
    input_path = Path(input_dir)
    metadata_list = []
    
    # Iterate through all files in the directory
    for file_path in input_path.iterdir():
        if file_path.is_file():
            try:
                # Open image using Pillow to extract properties
                with Image.open(file_path) as img:
                    width, height = img.size
                    metadata_list.append({
                        "filename": file_path.name,
                        "format": img.format,
                        "mode": img.mode,
                        "width": width,
                        "height": height,
                        "file_size_bytes": file_path.stat().st_size
                    })
            except (UnidentifiedImageError, OSError):
                # Skip non-image files or unreadable image formats
                continue

    # Return list sorted alphabetically by filename
    return sorted(metadata_list, key=lambda x: x["filename"])