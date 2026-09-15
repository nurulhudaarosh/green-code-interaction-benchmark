import os
from PIL import Image

def extract_metadata(input_dir):
    """
    Scan input_dir for image files and return metadata for each.

    Returns a list of dicts sorted by filename, each containing:
        filename, format, mode, width, height, file_size_bytes
    Corrupt/truncated/zero-byte files are reported as:
        {"filename": ..., "error": True}
    instead of crashing the scan.
    """
    valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
    results = []

    for entry in os.listdir(input_dir):
        path = os.path.join(input_dir, entry)
        if not os.path.isfile(path):
            continue
        if os.path.splitext(entry)[1].lower() not in valid_extensions:
            continue

        # Zero-byte files are trivially corrupt - no need to even try opening.
        if os.path.getsize(path) == 0:
            results.append({"filename": entry, "error": True})
            continue

        try:
            with Image.open(path) as img:
                # Image.open() is lazy: it only reads the header, so a
                # truncated file won't raise until the pixel data is
                # actually decoded. Force a full decode to catch that here.
                img.load()

                results.append({
                    "filename": entry,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "file_size_bytes": os.path.getsize(path),
                })
        except Exception:
            # Covers UnidentifiedImageError, OSError ("truncated"),
            # struct.error, and anything else raised during open/decode.
            results.append({"filename": entry, "error": True})

    return sorted(results, key=lambda d: d["filename"])