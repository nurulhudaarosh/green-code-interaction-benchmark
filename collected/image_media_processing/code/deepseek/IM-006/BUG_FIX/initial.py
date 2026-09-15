import os
from PIL import Image


def extract_metadata(input_dir):
    """
    Extract metadata from all images in input_dir.

    Returns a sorted list of dicts (sorted by filename), each containing:
        filename, format, mode, width, height, file_size_bytes
    """
    results = []

    for entry in os.scandir(input_dir):
        if not entry.is_file():
            continue

        filepath = entry.path
        try:
            with Image.open(filepath) as img:
                results.append({
                    "filename": entry.name,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "file_size_bytes": entry.stat().st_size,
                })
        except (UnidentifiedImageError, OSError):
            # Skip files that aren't valid images or can't be read
            continue

    return sorted(results, key=lambda d: d["filename"])