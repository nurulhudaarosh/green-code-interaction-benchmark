import os
from PIL import Image, UnidentifiedImageError


def extract_metadata(input_dir):
    """
    Extract metadata from all images in input_dir.

    Returns a sorted list of dicts (sorted by filename), each containing:
        filename, format, mode, width, height, file_size_bytes

    file_size_bytes is the actual on-disk file size, equal to
    os.path.getsize(path), NOT the decoded pixel buffer size.
    """
    results = []

    for entry in os.scandir(input_dir):
        if not entry.is_file():
            continue

        filepath = entry.path
        try:
            with Image.open(filepath) as img:
                # Read metadata from the header without decoding pixels.
                fmt = img.format
                mode = img.mode
                width, height = img.size

            # Actual on-disk size, matching os.path.getsize(filepath).
            file_size = os.path.getsize(filepath)

            results.append({
                "filename": entry.name,
                "format": fmt,
                "mode": mode,
                "width": width,
                "height": height,
                "file_size_bytes": file_size,
            })
        except (UnidentifiedImageError, OSError):
            continue

    return sorted(results, key=lambda d: d["filename"])