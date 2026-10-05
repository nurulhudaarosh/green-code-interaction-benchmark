from pathlib import Path
from PIL import Image, ImageOps


def build_contact_sheet(input_dir, output_path, thumb_size, columns):
    """
    Tile all images in input_dir into a contact sheet with a fixed
    number of columns.
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)

    if columns <= 0:
        raise ValueError("columns must be greater than 0")

    thumb_w, thumb_h = thumb_size

    supported = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}

    image_paths = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in supported
    )

    if not image_paths:
        raise ValueError("No supported images found in input_dir")

    n = len(image_paths)

    # Ceiling division: ensures a trailing partial row is included.
    rows = (n + columns - 1) // columns

    sheet = Image.new(
        "RGB",
        (columns * thumb_w, rows * thumb_h),
        "white"
    )

    for index, image_path in enumerate(image_paths):
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            thumbnail = ImageOps.contain(img, (thumb_w, thumb_h))

            col = index % columns
            row = index // columns

            x = col * thumb_w + (thumb_w - thumbnail.width) // 2
            y = row * thumb_h + (thumb_h - thumbnail.height) // 2

            sheet.paste(thumbnail, (x, y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)