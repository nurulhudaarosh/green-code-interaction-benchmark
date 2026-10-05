import math
from pathlib import Path

from PIL import Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}


def build_contact_sheet(
    input_dir,
    output_path,
    thumb_size,
    columns,
    padding=10,
    background=(255, 255, 255),
):
    """Tile every image in `input_dir` into a grid and save it to `output_path`.

    Args:
        input_dir:   Directory containing images (non-recursive, sorted by name).
        output_path: Where to save the contact sheet (format inferred from extension).
        thumb_size:  int (square cell) or (width, height) tuple for each cell.
        columns:     Fixed number of columns; rows are computed from image count.
        padding:     Pixels of space between cells and around the sheet edge.
        background:  Sheet background color (RGB tuple).

    Each image is scaled to fit inside its cell (aspect ratio preserved, never
    cropped) and centered. Unreadable files are skipped.

    Returns:
        The output path as a Path.
    """
    if columns < 1:
        raise ValueError("columns must be >= 1")

    if isinstance(thumb_size, int):
        thumb_w = thumb_h = thumb_size
    else:
        thumb_w, thumb_h = thumb_size
    if thumb_w < 1 or thumb_h < 1:
        raise ValueError("thumb_size must be positive")

    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    files = sorted(
        (p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS),
        key=lambda p: p.name.lower(),
    )

    thumbs = []
    for path in files:
        try:
            with Image.open(path) as im:
                im = ImageOps.exif_transpose(im)  # respect camera rotation
                im.thumbnail((thumb_w, thumb_h), Image.LANCZOS)
                if im.mode in ("RGBA", "LA", "P"):
                    im = im.convert("RGBA")
                    flat = Image.new("RGB", im.size, background)
                    flat.paste(im, mask=im.getchannel("A"))
                    im = flat
                else:
                    im = im.convert("RGB")
                thumbs.append(im.copy())
        except Exception as exc:  # corrupt / unsupported file
            print(f"Skipping {path.name}: {exc}")

    if not thumbs:
        raise ValueError(f"No readable images found in {input_dir}")

    cols = columns                          # fixed column count
    rows = math.ceil(len(thumbs) / cols)    # ceiling division: keeps the partial last row

    sheet_w = cols * thumb_w + (cols + 1) * padding
    sheet_h = rows * thumb_h + (rows + 1) * padding
    sheet = Image.new("RGB", (sheet_w, sheet_h), background)

    for i, thumb in enumerate(thumbs):
        row, col = divmod(i, cols)
        cell_x = padding + col * (thumb_w + padding)
        cell_y = padding + row * (thumb_h + padding)
        # center the thumbnail within its cell
        x = cell_x + (thumb_w - thumb.width) // 2
        y = cell_y + (thumb_h - thumb.height) // 2
        sheet.paste(thumb, (x, y))

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)
    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 5:
        sys.exit("usage: contact_sheet.py INPUT_DIR OUTPUT_PATH THUMB_SIZE COLUMNS")
    build_contact_sheet(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))