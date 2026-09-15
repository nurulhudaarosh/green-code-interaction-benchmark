id="58321"
import os
from pathlib import Path
from PIL import Image


def extract_metadata(input_dir):
    input_path = Path(input_dir)
    metadata = []

    for path in input_path.iterdir():
        if not path.is_file():
            continue

        try:
            with Image.open(path) as img:
                metadata.append({
                    "filename": path.name,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "file_size_bytes": os.path.getsize(path)
                })
        except (OSError, ValueError):
            # Skip files that are not valid images
            continue

    return sorted(metadata, key=lambda x: x["filename"])