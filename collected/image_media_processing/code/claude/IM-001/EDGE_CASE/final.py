import os
from pathlib import Path
from PIL import Image

def batch_resize(input_dir, output_dir, target_size):
    """
    Resize every PNG/JPEG image in input_dir to target_size and save to output_dir.

    Args:
        input_dir: path to folder containing source images
        output_dir: path to folder where resized images will be saved
        target_size: (width, height) tuple

    Returns:
        dict: {
            'processed_count': int,
            'skipped': [{'file': str, 'reason': str}, ...]
        }
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    result = {'processed_count': 0, 'skipped': []}

    # No valid input directory -> nothing to process, no error
    if not input_dir.exists() or not input_dir.is_dir():
        return result

    valid_extensions = {".png", ".jpg", ".jpeg"}

    # Collect candidate files first so an empty/non-matching dir is a clean no-op
    candidates = [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in valid_extensions
    ]

    if not candidates:
        return result

    output_dir.mkdir(parents=True, exist_ok=True)

    for file_path in candidates:
        try:
            with Image.open(file_path) as img:
                if file_path.suffix.lower() in {".jpg", ".jpeg"} and img.mode != "RGB":
                    img = img.convert("RGB")

                resized = img.resize(target_size, Image.LANCZOS)
                resized.save(output_dir / file_path.name)
                result['processed_count'] += 1
        except Exception as e:
            result['skipped'].append({'file': file_path.name, 'reason': str(e)})

    return result