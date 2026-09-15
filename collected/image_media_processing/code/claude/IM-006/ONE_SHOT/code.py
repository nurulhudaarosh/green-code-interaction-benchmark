import os
from PIL import Image

def extract_metadata(input_dir):
    """
    Scan input_dir for image files and return a sorted list of dicts with
    filename, format, mode, width, height, and file_size_bytes.

    Sorted by filename (alphabetically).
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
            # Not a valid image file (or unreadable) — skip it
            continue

    results.sort(key=lambda d: d["filename"])
    return results