import os
from PIL import Image, UnidentifiedImageError


def extract_metadata(input_dir):
    """
    Extract metadata for every image in input_dir.

    Returns a list of dicts sorted by filename, each containing:
        filename, format, mode, width, height, file_size_bytes
    """
    results = []

    for entry in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, entry)
        if not os.path.isfile(path):
            continue

        try:
            with Image.open(path) as img:
                results.append({
                    "filename": entry,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "file_size_bytes": os.path.getsize(path),
                })
        except (UnidentifiedImageError, OSError):
            # Not a valid image or unreadable — skip it
            continue

    return results