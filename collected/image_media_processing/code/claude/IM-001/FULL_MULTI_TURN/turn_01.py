import os
from pathlib import Path
from PIL import Image

def batch_resize(input_dir, output_dir, target_size):
    """
    Resize every PNG/JPEG image in input_dir to target_size and save to output_dir.

    Args:
        input_dir (str): Directory containing source images.
        output_dir (str): Directory to save resized images (created if missing).
        target_size (tuple[int, int]): Desired (width, height) in pixels.

    Returns:
        int: Number of images successfully processed.
    """
    valid_exts = {".png", ".jpg", ".jpeg"}
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    count = 0
    for file in input_path.iterdir():
        if file.suffix.lower() not in valid_exts or not file.is_file():
            continue
        try:
            with Image.open(file) as img:
                resized = img.resize(target_size, Image.LANCZOS)
                # Preserve mode/format issues: convert RGBA->RGB for JPEG output
                if file.suffix.lower() in {".jpg", ".jpeg"} and resized.mode in ("RGBA", "P"):
                    resized = resized.convert("RGB")
                dest = output_path / file.name
                resized.save(dest)
                count += 1
        except Exception as e:
            print(f"Skipping {file.name}: {e}")

    return count