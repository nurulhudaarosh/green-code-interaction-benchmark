"""Contact sheet builder: tiles every image in a folder into a fixed-column grid."""

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}


def _load_font(size):
    """Best available font at `size`; falls back to Pillow's bitmap default."""
    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10.1
    except TypeError:
        pass
    for name in ("DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fit_text(draw, text, font, max_width):
    """Shorten `text` with '...' so it fits within `max_width` pixels."""
    if draw.textlength(text, font=font) <= max_width:
        return text
    while len(text) > 1 and draw.textlength(text + "...", font=font) > max_width:
        text = text[:-1]
    return text + "..."


def build_contact_sheet(input_dir, output_path, thumb_size=(200, 200), columns=5,
                        padding=10, background=(255, 255, 255),
                        label=True, label_font_size=12, label_color=(40, 40, 40)):
    """Tile all images in `input_dir` into a grid and save it to `output_path`.

    Args:
        input_dir:       Directory containing images (non-recursive, sorted by name).
        output_path:     Where to save the sheet (format inferred from extension).
        thumb_size:      int or (width, height) of each thumbnail area; images are
                         scaled to fit inside it, preserving aspect ratio, and centered.
        columns:         Fixed number of columns; row count is derived.
        padding:         Pixels between cells and around the border.
        background:      Background color of the sheet.
        label:           If True, draw each filename in a caption strip beneath its
                         thumbnail. The strip is added to each cell's height, so the
                         thumbnail area stays `thumb_size`. Long names are truncated
                         with '...' to fit the cell width.
        label_font_size: Caption font size in px.
        label_color:     Caption text color.

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

    thumbs = []  # (filename, thumbnail)
    for p in paths:
        try:
            with Image.open(p) as img:
                img = ImageOps.exif_transpose(img)  # respect camera rotation
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")
                img.thumbnail((tw, th), Image.LANCZOS)
                thumbs.append((p.name, img.copy()))
        except (UnidentifiedImageError, OSError) as e:
            print(f"Skipping {p.name}: {e}", file=sys.stderr)

    if not thumbs:
        raise ValueError(f"No readable images found in {input_dir}")

    # Reserve a caption strip under each thumbnail area if labeling.
    font = _load_font(label_font_size) if label else None
    caption_gap = 4
    caption_h = 0
    if label:
        caption_h = font.getbbox("Ag")[3] + caption_gap + 2  # glyph bottom + spacing
    cell_w, cell_h = tw, th + caption_h

    rows = math.ceil(len(thumbs) / columns)
    sheet_w = columns * cell_w + (columns + 1) * padding
    sheet_h = rows * cell_h + (rows + 1) * padding
    sheet = Image.new("RGB", (sheet_w, sheet_h), background)
    draw = ImageDraw.Draw(sheet)

    for i, (name, thumb) in enumerate(thumbs):
        row, col = divmod(i, columns)
        cell_x = padding + col * (cell_w + padding)
        cell_y = padding + row * (cell_h + padding)

        x = cell_x + (tw - thumb.width) // 2
        y = cell_y + (th - thumb.height) // 2
        mask = thumb.getchannel("A") if thumb.mode == "RGBA" else None
        sheet.paste(thumb, (x, y), mask)

        if label:
            text = _fit_text(draw, name, font, cell_w)
            text_w = draw.textlength(text, font=font)
            draw.text((cell_x + (cell_w - text_w) / 2, cell_y + th + caption_gap),
                      text, fill=label_color, font=font)

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
    ap.add_argument("--no-label", action="store_true", help="omit filename captions")
    args = ap.parse_args()
    n = build_contact_sheet(args.input_dir, args.output_path, args.thumb, args.columns,
                            label=not args.no_label)
    print(f"Placed {n} images in {args.output_path}")