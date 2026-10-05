from PIL import Image
import os
import math


def build_contact_sheet(input_dir, output_path, thumb_size, columns):
    """
    Tile all images from input_dir into a grid contact sheet.

    Returns:
        tuple: (number_of_rows, columns)
    """
    valid_exts = {
        ".jpg", ".jpeg", ".png", ".bmp",
        ".gif", ".webp", ".tiff"
    }

    if columns <= 0:
        raise ValueError("columns must be greater than 0.")

    thumb_w, thumb_h = thumb_size

    image_files = sorted(
        f for f in os.listdir(input_dir)
        if os.path.splitext(f)[1].lower() in valid_exts
    )

    # Handle empty input directory.
    if not image_files:
        rows = 0

        # Minimal valid image: one-pixel-high canvas.
        sheet = Image.new("RGB", (max(1, columns * thumb_w), 1), "white")

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        sheet.save(output_path)

        return rows, columns

    # Ceiling division ensures a trailing partial row is included.
    rows = math.ceil(len(image_files) / columns)

    sheet_w = columns * thumb_w
    sheet_h = rows * thumb_h

    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")

    for index, filename in enumerate(image_files):
        path = os.path.join(input_dir, filename)

        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((thumb_w, thumb_h))

            cell_x = (index % columns) * thumb_w
            cell_y = (index // columns) * thumb_h

            # Center thumbnail within its cell.
            offset_x = (thumb_w - img.width) // 2
            offset_y = (thumb_h - img.height) // 2

            sheet.paste(
                img,
                (cell_x + offset_x, cell_y + offset_y)
            )

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    sheet.save(output_path)

    return rows, columns