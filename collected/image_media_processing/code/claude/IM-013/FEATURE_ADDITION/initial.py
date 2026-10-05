"""Contact sheet builder: tiles every image in a folder into a fixed-column grid."""

import math
import sys
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}


def build_contact_sheet(input_dir, output_path, thumb_size=(200, 200), columns=5,
                        padding=10, background=(255, 255, 255)):
    """Tile all images in `input_dir` into a grid and save it to `output_path`.

    Args:
        input_dir:   Directory containing images (non-recursive, sorted by name).
        output_path: Where to save the sheet (format inferred from extension).
        thumb_size:  int or (width, height) of each cell; images are scaled to
                     fit inside it, preserving aspect ratio, and centered.
        columns:     Fixed number of columns; row count is derived.
        padding:     Pixels between cells and around the border.
        background:  Background color of the sheet.

    Returns:
        The number of images placed on the sheet.
    """
    if columns < 1:
        raise ValueError("columns must be >= 1")
    if isinstance(thumb_size, int):
        thumb_size = (thumb_size, thumb_size)
    tw, th = thumb_size
    if tw < 1 or th < 1:
        raise ValueError("thumb_size must be positive")

    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    out = Path(output_path).resolve()
    paths = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS and p.resolve() != out
    )

    thumbs = []
    for p in paths:
        try:
            with Image.open(p) as img:
                img = ImageOps.exif_transpose(img)  # respect camera rotation
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")
                img.thumbnail((tw, th), Image.LANCZOS)
                thumbs.append(img.copy())
        except (UnidentifiedImageError, OSError) as e:
            print(f"Skipping {p.name}: {e}", file=sys.stderr)

    if not thumbs:
        raise ValueError(f"No readable images found in {input_dir}")

    rows = math.ceil(len(thumbs) / columns)
    sheet_w = columns * tw + (columns + 1) * padding
    sheet_h = rows * th + (rows + 1) * padding
    sheet = Image.new("RGB", (sheet_w, sheet_h), background)

    for i, thumb in enumerate(thumbs):
        row, col = divmod(i, columns)
        x = padding + col * (tw + padding) + (tw - thumb.width) // 2
        y = padding + row * (th + padding) + (th - thumb.height) // 2
        mask = thumb.getchannel("A") if thumb.mode == "RGBA" else None
        sheet.paste(thumb, (x, y), mask)

    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return len(thumbs)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Build an image contact sheet.")
    ap.add_argument("input_dir")
    ap.add_argument("output_path")
    ap.add_argument("--thumb", type=int, default=200, help="square cell size in px")
    ap.add_argument("--columns", type=int, default=5)
    args = ap.parse_args()
    n = build_contact_sheet(args.input_dir, args.output_path, args.thumb, args.columns)
    print(f"Placed {n} images in {args.output_path}")