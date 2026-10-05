from pathlib import Path
from PIL import Image, ImageOps


def build_contact_sheet(input_dir, output_path, thumb_size, columns):
    """
    Tile all images in input_dir into a contact sheet with a fixed
    number of columns.

    Args:
        input_dir (str): Directory containing input images.
        output_path (str): Path where the contact sheet will be saved.
        thumb_size (tuple): Thumbnail size as (width, height).
        columns (int): Number of columns in the grid.
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)

    if columns <= 0:
        raise ValueError("columns must be greater than 0")

    if len(thumb_size) != 2 or thumb_size[0] <= 0 or thumb_size[1] <= 0:
        raise ValueError("thumb_size must be a positive (width, height) tuple")

    supported = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}

    image_paths = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in supported
    )

    if not image_paths:
        raise ValueError("No supported images found in input_dir")

    thumb_w, thumb_h = thumb_size
    rows = (len(image_paths) + columns - 1) // columns

    sheet = Image.new(
        "RGB",
        (columns * thumb_w, rows * thumb_h),
        "white"
    )

    for index, image_path in enumerate(image_paths):
        with Image.open(image_path) as img:
            img = img.convert("RGB")

            # Preserve aspect ratio and fit entirely inside the thumbnail.
            thumbnail = ImageOps.contain(img, (thumb_w, thumb_h))

            # Center the thumbnail within its cell.
            x = index % columns
            y = index // columns

            offset_x = (thumb_w - thumbnail.width) // 2
            offset_y = (thumb_h - thumbnail.height) // 2

            sheet.paste(
                thumbnail,
                (
                    x * thumb_w + offset_x,
                    y * thumb_h + offset_y
                )
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)