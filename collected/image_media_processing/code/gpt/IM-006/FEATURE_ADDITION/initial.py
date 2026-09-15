import os
from PIL import Image


def extract_metadata(input_dir):
    metadata = []

    for filename in os.listdir(input_dir):
        path = os.path.join(input_dir, filename)

        if not os.path.isfile(path):
            continue

        try:
            with Image.open(path) as img:
                metadata.append({
                    "filename": filename,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "file_size_bytes": os.path.getsize(path),
                })
        except (OSError, ValueError):
            # Skip files that are not valid images
            continue

    return sorted(metadata, key=lambda x: x["filename"])