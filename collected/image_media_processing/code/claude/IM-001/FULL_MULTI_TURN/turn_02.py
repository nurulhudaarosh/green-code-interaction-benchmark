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
        if not file.is_file() or file.suffix.lower() not in valid_exts:
            continue

        try:
            with Image.open(file) as img:
                # Explicitly create a NEW resized image object
                resized_img = img.resize(target_size, Image.LANCZOS)

                # JPEG can't hold alpha/palette — convert before saving
                if file.suffix.lower() in {".jpg", ".jpeg"} and resized_img.mode in ("RGBA", "P"):
                    resized_img = resized_img.convert("RGB")

                dest = output_path / file.name

                # Save the RESIZED image, not the original `img`
                resized_img.save(dest)

            # Sanity check: confirm the saved file actually has target_size
            with Image.open(dest) as check_img:
                if check_img.size != tuple(target_size):
                    print(f"Warning: {dest.name} size mismatch after save "
                          f"(got {check_img.size}, expected {target_size})")
                else:
                    count += 1

        except Exception as e:
            print(f"Skipping {file.name}: {e}")

    return count