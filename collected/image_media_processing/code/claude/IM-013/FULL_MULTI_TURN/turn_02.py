import math
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}


def build_contact_sheet(input_dir, output_path, thumb_size, columns,
                        padding=10, background=(255, 255, 255)):
    """Tile all images in input_dir into a grid and save it to output_path.

    thumb_size: int (square cell) or (width, height) tuple. Each image is
                scaled to fit within the cell, preserving aspect ratio, and
                centered.
    columns:    fixed number of columns; row count is derived using ceiling
                division so a trailing partial row is always included.
    """
    if columns < 1:
        raise ValueError("columns must be >= 1")
    cell_w, cell_h = (thumb_size, thumb_size) if isinstance(thumb_size, int) else thumb_size

    paths = sorted(p for p in Path(input_dir).iterdir()
                   if p.is_file() and p.suffix.lower() in IMAGE_EXTS)

    thumbs = []
    for path in paths:
        try:
            with Image.open(path) as im:
                im = ImageOps.exif_transpose(im)  # respect camera orientation
                has_alpha = "A" in im.getbands() or "transparency" in im.info
                im = im.convert("RGBA" if has_alpha else "RGB")
                im.thumbnail((cell_w, cell_h), Image.LANCZOS)
                thumbs.append(im.copy())
        except (UnidentifiedImageError, OSError) as e:
            print(f"Skipping {path.name}: {e}")  # unreadable / corrupt file
            continue

    if not thumbs:
        raise ValueError(f"No readable images found in {input_dir}")

    rows = math.ceil(len(thumbs) / columns)  # ceiling division: keeps partial last row
    sheet_w = columns * cell_w + (columns + 1) * padding
    sheet_h = rows * cell_h + (rows + 1) * padding
    sheet = Image.new("RGB", (sheet_w, sheet_h), background)

    for i, thumb in enumerate(thumbs):
        row, col = divmod(i, columns)
        x = padding + col * (cell_w + padding) + (cell_w - thumb.width) // 2
        y = padding + row * (cell_h + padding) + (cell_h - thumb.height) // 2
        mask = thumb if thumb.mode == "RGBA" else None  # keep transparency
        sheet.paste(thumb, (x, y), mask)

    sheet.save(output_path)
    return sheet


if __name__ == "__main__":
    build_contact_sheet("photos", "contact_sheet.jpg", 200, 5)