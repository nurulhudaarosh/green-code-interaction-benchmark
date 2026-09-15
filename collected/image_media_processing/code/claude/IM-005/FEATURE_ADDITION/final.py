from pathlib import Path
from PIL import Image, ImageFilter

def apply_blur(input_dir, output_dir, radius, filter_type="gaussian"):
    if radius < 0:
        raise ValueError(f"radius must be >= 0, got {radius}")

    filter_type = filter_type.lower()
    if filter_type not in ("gaussian", "box"):
        raise ValueError(
            f"filter_type must be 'gaussian' or 'box', got {filter_type!r}"
        )

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
            elif filter_type == "gaussian":
                result = img.filter(ImageFilter.GaussianBlur(radius=radius))
            else:  # "box"
                result = img.filter(ImageFilter.BoxBlur(radius))

            result.save(output_dir / path.name)