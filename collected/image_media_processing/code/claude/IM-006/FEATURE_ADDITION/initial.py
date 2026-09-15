import os
from PIL import Image

def extract_metadata(input_dir):
    """
    Extract metadata for every image file in input_dir.

    Returns a list of dicts, sorted by filename, each containing:
        - filename
        - format
        - mode
        - width
        - height
        - file_size_bytes
    """
    results = []

    for entry in os.listdir(input_dir):
        full_path = os.path.join(input_dir, entry)

        if not os.path.isfile(full_path):
            continue

        try:
            with Image.open(full_path) as img:
                width, height = img.size
                results.append({
                    "filename": entry,
                    "format": img.format,
                    "mode": img.mode,
                    "width": width,
                    "height": height,
                    "file_size_bytes": os.path.getsize(full_path),
                })
        except (IOError, OSError):
            # Not a valid/openable image file — skip it
            continue

    results.sort(key=lambda d: d["filename"])
    return results