import os
from PIL import Image, UnidentifiedImageError


def extract_metadata(input_dir):
    """
    Extract metadata for every image in input_dir.

    Returns a list of dicts sorted by filename. Valid images contain:
        filename, format, mode, width, height, file_size_bytes, aspect_ratio, error
    Corrupt/truncated/zero-byte files contain:
        filename, file_size_bytes, error

    A zero-byte or truncated image file is caught as corrupt and reported with
    'error': True rather than crashing the whole scan.
    """
    results = []

    for entry in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, entry)
        if not os.path.isfile(path):
            continue

        file_size_bytes = os.path.getsize(path)

        # A zero-byte file can never be a valid image — flag it up front.
        if file_size_bytes == 0:
            results.append({
                "filename": entry,
                "file_size_bytes": file_size_bytes,
                "error": True,
            })
            continue

        try:
            with Image.open(path) as img:
                width = img.width
                height = img.height
                # Force a full decode so truncated files raise here rather than
                # silently returning header-only metadata.
                img.load()

                results.append({
                    "filename": entry,
                    "format": img.format,
                    "mode": img.mode,
                    "width": width,
                    "height": height,
                    "file_size_bytes": file_size_bytes,
                    "aspect_ratio": round(width / height, 3) if height else None,
                    "error": False,
                })
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
            # Not a valid image, unreadable, or truncated — report, don't crash.
            results.append({
                "filename": entry,
                "file_size_bytes": file_size_bytes,
                "error": True,
            })

    return results