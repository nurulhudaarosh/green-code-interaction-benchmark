id="58321"
from pathlib import Path
from PIL import Image

def batch_resize(input_dir, output_dir, target_size):
    """
    Resize every PNG/JPEG image in input_dir to target_size.

    Returns:
        dict: {
            'processed_count': number of successfully processed images,
            'skipped': list of filenames that could not be processed
        }
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_extensions = {".png", ".jpg", ".jpeg"}
    skipped = []
    processed_count = 0

    # Handle empty/non-existent input directories safely.
    if not input_dir.exists() or not input_dir.is_dir():
        return {"processed_count": 0, "skipped": []}

    image_files = [
        path for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in valid_extensions
    ]

    # Empty directory or no valid image files.
    if not image_files:
        return {"processed_count": 0, "skipped": []}

    for image_path in image_files:
        try:
            with Image.open(image_path) as img:
                resized = img.resize(target_size)
                output_path = output_dir / image_path.name
                resized.save(output_path)

            processed_count += 1

        except (OSError, ValueError):
            skipped.append(image_path.name)

    return {
        "processed_count": processed_count,
        "skipped": skipped
    }