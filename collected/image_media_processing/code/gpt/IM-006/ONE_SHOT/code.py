from pathlib import Path
from PIL import Image


def extract_metadata(input_dir):
    input_path = Path(input_dir)
    metadata = []

    for file_path in input_path.iterdir():
        if not file_path.is_file():
            continue

        try:
            with Image.open(file_path) as img:
                metadata.append({
                    "filename": file_path.name,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "file_size_bytes": file_path.stat().st_size
                })
        except (OSError, ValueError):
            # Skip files that are not valid images
            continue

    return sorted(metadata, key=lambda x: x["filename"])