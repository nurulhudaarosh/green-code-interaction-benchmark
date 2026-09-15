import os
from PIL import Image, UnidentifiedImageError


def extract_metadata(input_dir):
    """
    Extract metadata from all images in input_dir.

    Returns a sorted list of dicts with keys:
        filename, format, mode, width, height, file_size_bytes, error

    Files that cannot be opened/decoded (zero-byte, truncated, or non-image)
    are included with 'error': True and all other fields set to None.
    """
    metadata = []

    for entry in os.scandir(input_dir):
        if not entry.is_file():
            continue

        file_path = entry.path
        file_size = entry.stat().st_size

        # Zero-byte files can't be valid images — report without opening.
        if file_size == 0:
            metadata.append({
                "filename": entry.name,
                "format": None,
                "mode": None,
                "width": None,
                "height": None,
                "file_size_bytes": 0,
                "error": True,
            })
            continue

        try:
            with Image.open(file_path) as img:
                # Force decode so truncated files raise here rather than later.
                img.load()
                metadata.append({
                    "filename": entry.name,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "file_size_bytes": file_size,
                    "error": False,
                })
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
            # Corrupt, truncated, or non-image file — record as an error entry.
            metadata.append({
                "filename": entry.name,
                "format": None,
                "mode": None,
                "width": None,
                "height": None,
                "file_size_bytes": file_size,
                "error": True,
            })

    metadata.sort(key=lambda m: m["filename"])
    return metadata