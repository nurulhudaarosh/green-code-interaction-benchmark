from pathlib import Path
from PIL import Image, ImageOps


def build_contact_sheet(input_dir, output_path, thumb_size, columns):
    """
    Create a contact sheet by tiling all images in input_dir into a grid.

    Args:
        input_dir: Directory containing input images.
        output_path: Path where the contact sheet will be saved.
        thumb_size: (width, height) of each thumbnail cell.
        columns: Number of columns in the grid.
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)

    if columns <= 0:
        raise ValueError("columns must be greater than 0")

    thumb_w, thumb_h = thumb_size
    if thumb_w <= 0 or thumb_h <= 0:
        raise ValueError("thumb_size dimensions must be greater than 0")

    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}

    image_paths = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in image_extensions
    )

    if not image_paths:
        raise ValueError("No images found in input_dir")

    rows = (len(image_paths) + columns - 1) // columns

    sheet_width = columns * thumb_w
    sheet_height = rows * thumb_h

    # White background for the contact sheet
    sheet = Image.new("RGB", (sheet_width, sheet_height), "white")

    for index, image_path in enumerate(image_paths):
        with Image.open(image_path) as img:
            img = img.convert("RGB")

            # Preserve aspect ratio and fit inside the thumbnail cell.
            thumbnail = ImageOps.contain(img, (thumb_w, thumb_h))

            # Center the thumbnail within its cell.
            x_offset = (thumb_w - thumbnail.width) // 2
            y_offset = (thumb_h - thumbnail.height) // 2

            cell_x = (index % columns) * thumb_w
            cell_y = (index // columns) * thumb_h

            sheet.paste(
                thumbnail,
                (cell_x + x_offset, cell_y + y_offset)
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)