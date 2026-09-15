import os
from PIL import Image

def extract_metadata(input_dir):
    """
    Scan input_dir for image files and return metadata for each.

    Returns a list of dicts sorted by filename, each containing:
        filename, format, mode, width, height, file_size_bytes
    """
    valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
    results = []

    for entry in os.listdir(input_dir):
        path = os.path.join(input_dir, entry)
        if not os.path.isfile(path):
            continue
        if os.path.splitext(entry)[1].lower() not in valid_extensions:
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
        except Exception:
            # Skip files that aren't valid images
            continue

    return sorted(results, key=lambda d: d["filename"])