import os
from PIL import Image


def extract_metadata(input_dir):
    """
    Extract metadata from all images in input_dir.

    Returns a sorted list of dicts with keys:
        filename, format, mode, width, height, file_size_bytes
    """
    metadata = []

    for entry in os.scandir(input_dir):
        if not entry.is_file():
            continue

        file_path = entry.path
        try:
            with Image.open(file_path) as img:
                # Force loading so truncated files raise here
                img.load()
                metadata.append({
                    "filename": entry.name,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "file_size_bytes": entry.stat().st_size,
                })
        except (UnidentifiedImageError, OSError):
            # Not an image or unreadable — skip
            continue

    metadata.sort(key=lambda m: m["filename"])
    return metadata