from pathlib import Path
from PIL import Image, ImageFilter

def apply_blur(input_dir, output_dir, radius):
    if radius < 0:
        raise ValueError(f"radius must be >= 0, got {radius}")

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}

    for path in input_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in exts:
            continue

        with Image.open(path) as img:
            if radius == 0:
                result = img.copy()
            else:
                result = img.filter(ImageFilter.GaussianBlur(radius=radius))

            result.save(output_dir / path.name)