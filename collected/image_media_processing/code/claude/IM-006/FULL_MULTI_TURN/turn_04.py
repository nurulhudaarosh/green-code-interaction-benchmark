import os
from PIL import Image, UnidentifiedImageError


def extract_metadata(input_dir):
    """
    Extract metadata for every image file in input_dir.

    Returns a list of dicts sorted by filename. Each dict normally contains:
        filename, format, mode, width, height, file_size_bytes, aspect_ratio

    If a file is zero-byte, truncated, or otherwise unreadable as an image,
    its dict instead contains:
        filename, error (True), error_message, file_size_bytes
    """
    results = []

    for entry in os.listdir(input_dir):
        full_path = os.path.join(input_dir, entry)

        if not os.path.isfile(full_path):
            continue

        file_size_bytes = os.path.getsize(full_path)

        try:
            with Image.open(full_path) as img:
                # Force full decode now, so truncated files raise here
                # rather than surfacing an error later when pixels are read.
                img.load()

                width, height = img.width, img.height
                aspect_ratio = round(width / height, 3) if height else None

                results.append({
                    "filename": entry,
                    "format": img.format,
                    "mode": img.mode,
                    "width": width,
                    "height": height,
                    "file_size_bytes": file_size_bytes,
                    "aspect_ratio": aspect_ratio,
                })
        except (UnidentifiedImageError, OSError, IOError, SyntaxError, ValueError) as e:
            # Covers: zero-byte files, truncated files, corrupt headers,
            # and files that aren't actually images.
            results.append({
                "filename": entry,
                "error": True,
                "error_message": str(e),
                "file_size_bytes": file_size_bytes,
            })

    results.sort(key=lambda d: d["filename"])
    return results