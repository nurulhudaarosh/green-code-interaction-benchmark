import os
from PIL import Image, UnidentifiedImageError

def extract_metadata(input_dir):
    """
    Extract metadata from all images in a directory.

    Returns a sorted list of dicts with:
        filename, format, mode, width, height, file_size_bytes, aspect_ratio
    """
    results = []

    for entry in os.scandir(input_dir):
        if not entry.is_file():
            continue
        try:
            with Image.open(entry.path) as img:
                width = img.width
                height = img.height
                info = {
                    "filename": entry.name,
                    "format": img.format,
                    "mode": img.mode,
                    "width": width,
                    "height": height,
                    "file_size_bytes": entry.stat().st_size,
                    "aspect_ratio": round(width / height, 3) if height else None,
                }
        except (UnidentifiedImageError, OSError):
            # Skip files that aren't valid images
            continue
        results.append(info)

    results.sort(key=lambda d: d["filename"])
    return results