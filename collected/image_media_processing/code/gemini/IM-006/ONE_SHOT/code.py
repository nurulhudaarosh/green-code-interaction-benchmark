import os
from pathlib import Path
from PIL import Image

def extract_metadata(input_dir):
    image_metadata = []
    input_path = Path(input_dir)

    if not input_path.exists() or not input_path.is_dir():
        raise ValueError(f"Invalid directory path: {input_dir}")

    for entry in input_path.iterdir():
        if entry.is_file():
            try:
                # Open image using Pillow
                with Image.open(entry) as img:
                    metadata = {
                        "filename": entry.name,
                        "format": img.format,
                        "mode": img.mode,
                        "width": img.width,
                        "height": img.height,
                        "file_size_bytes": entry.stat().st_size
                    }
                    image_metadata.append(metadata)
            except (IOError, SyntaxError):
                # Ignore non-image files or corrupted images
                continue

    # Sort the list of dicts alphabetically by filename
    return sorted(image_metadata, key=lambda x: x["filename"])