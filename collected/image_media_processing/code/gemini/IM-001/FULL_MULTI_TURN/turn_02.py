from pathlib import Path
from PIL import Image

def batch_resize(input_dir: str | Path, output_dir: str | Path, target_size: tuple[int, int]) -> int:
    """
    Resizes all PNG and JPEG images in input_dir to target_size and saves the resized images to output_dir.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    valid_extensions = {".png", ".jpg", ".jpeg"}
    processed_count = 0

    for file_path in input_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            try:
                with Image.open(file_path) as img:
                    # Note: img.resize() does NOT modify `img` in place; it returns a new Image object.
                    # We must store the result and call .save() on this new object.
                    resized_img = img.resize(target_size, resample=Image.Resampling.LANCZOS)
                    
                    # Convert transparent/palette modes to RGB if target format is JPEG
                    out_ext = file_path.suffix.lower()
                    if out_ext in {".jpg", ".jpeg"} and resized_img.mode in ("RGBA", "LA", "P"):
                        resized_img = resized_img.convert("RGB")

                    destination = output_path / file_path.name
                    
                    # Ensure we save `resized_img`, NOT `img`
                    resized_img.save(destination)
                    processed_count += 1
            except Exception as e:
                print(f"Skipping {file_path.name} due to error: {e}")

    return processed_count