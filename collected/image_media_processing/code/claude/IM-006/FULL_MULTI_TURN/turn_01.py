import os
from PIL import Image


def extract_metadata(input_dir):
    """
    Extract metadata for every image file in input_dir.

    Args:
        input_dir (str): Path to the directory containing images.

    Returns:
        list[dict]: A list of dicts, each containing:
            - filename (str): the image file's name
            - format (str): image format (e.g. 'JPEG', 'PNG')
            - mode (str): image mode (e.g. 'RGB', 'RGBA', 'L')
            - width (int): image width in pixels
            - height (int): image height in pixels
            - file_size_bytes (int): size of the file on disk in bytes
        Sorted by filename.
    """
    results = []

    for entry in os.listdir(input_dir):
        full_path = os.path.join(input_dir, entry)

        if not os.path.isfile(full_path):
            continue

        try:
            with Image.open(full_path) as img:
                results.append({
                    "filename": entry,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "file_size_bytes": os.path.getsize(full_path),
                })
        except (IOError, SyntaxError):
            # Not a valid/readable image file — skip it
            continue

    results.sort(key=lambda d: d["filename"])
    return results