id="58321"
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def build_contact_sheet(
    input_dir,
    output_path,
    thumb_size,
    columns,
    label=True
):
    """
    Tile all valid images into a contact sheet.

    Args:
        input_dir: Directory containing images.
        output_path: Output contact sheet path.
        thumb_size: (width, height) of each thumbnail area.
        columns: Number of columns.
        label: If True, draw each filename below its thumbnail.

    Returns:
        (number_of_images, columns)
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)

    if columns <= 0:
        raise ValueError("columns must be greater than 0")

    thumb_w, thumb_h = thumb_size

    if thumb_w <= 0 or thumb_h <= 0:
        raise ValueError("thumb_size dimensions must be greater than 0")

    valid_extensions = {
        ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"
    }

    images = []

    for path in sorted(input_dir.iterdir()):
        if path.suffix.lower() not in valid_extensions:
            continue

        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
                img.thumbnail((thumb_w, thumb_h))
                images.append((path.name, img.copy()))
        except (OSError, ValueError):
            continue

    n = len(images)

    # Ceiling division includes a trailing partial row.
    rows = (n + columns - 1) // columns

    # Caption strip height.
    caption_height = 20 if label else 0
    cell_height = thumb_h + caption_height

    # Handle zero valid images.
    if n == 0:
        sheet = Image.new("RGB", (1, 1), "white")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output_path)
        return 0, columns

    sheet_width = columns * thumb_w
    sheet_height = rows * cell_height

    sheet = Image.new("RGB", (sheet_width, sheet_height), "white")
    draw = ImageDraw.Draw(sheet)

    for i, (filename, img) in enumerate(images):
        row = i // columns
        col = i % columns

        cell_x = col * thumb_w
        cell_y = row * cell_height

        # Center thumbnail inside its thumbnail area.
        x = cell_x + (thumb_w - img.width) // 2
        y = cell_y + (thumb_h - img.height) // 2

        sheet.paste(img, (x, y))

        if label:
            # Draw filename centered in the reserved caption strip.
            text_bbox = draw.textbbox((0, 0), filename)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            text_x = cell_x + (thumb_w - text_width) // 2
            text_y = (
                cell_y
                + thumb_h
                + (caption_height - text_height) // 2
            )

            draw.text((text_x, text_y), filename, fill="black")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)

    return n, columns