import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def build_contact_sheet(input_dir, output_path, thumb_size=(200, 200),
                        columns=4, label=True, label_font_size=12,
                        label_max_chars=None):
    """
    Create a contact sheet by tiling all images from input_dir into a grid.

    Args:
        input_dir (str): Directory containing images.
        output_path (str): Path where the contact sheet will be saved.
        thumb_size (tuple): (width, height) of each thumbnail's image area.
        columns (int): Number of columns in the grid.
        label (bool): If True, draw each image's filename as a caption
            beneath its thumbnail. A caption strip is reserved in each cell.
        label_font_size (int): Point size for the caption font.
        label_max_chars (int|None): Truncate labels longer than this.
            If None, derive a limit from the thumbnail width.

    Returns:
        bool: True if successful, False otherwise.
    """
    if columns < 1:
        raise ValueError("columns must be >= 1")

    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist")

    image_files = [
        f for f in sorted(input_path.iterdir())
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    if not image_files:
        raise ValueError(f"No image files found in '{input_dir}'")

    num_images = len(image_files)

    # Ceiling division: include any trailing partial row.
    rows = (num_images + columns - 1) // columns

    padding = 10
    thumb_width, thumb_height = thumb_size

    # --- Set up font and caption strip BEFORE computing canvas size ---
    font = None
    caption_height = 0

    if label:
        try:
            font = ImageFont.truetype("arial.ttf", label_font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Measure the strip height from the font's own metrics so it always
        # fits the glyphs plus a few pixels of breathing room.
        try:
            ascent, descent = font.getmetrics()
            text_h = ascent + descent
        except AttributeError:
            # Older Pillow / bitmap font fallback
            bbox = font.getbbox("Ag")
            text_h = bbox[3] - bbox[1] if bbox else label_font_size

        caption_height = text_h + 6  # +6 px for a little top/bottom margin

    # Cell height = thumbnail area + optional caption strip.
    cell_height = thumb_height + caption_height

    canvas_width = (columns * thumb_width) + ((columns + 1) * padding)
    canvas_height = (rows * cell_height) + ((rows + 1) * padding)

    contact_sheet = Image.new('RGB', (canvas_width, canvas_height), 'white')
    draw = ImageDraw.Draw(contact_sheet)

    for idx, image_path in enumerate(image_files):
        row = idx // columns
        col = idx % columns

        # Top-left of the whole cell (thumbnail + caption strip).
        cell_x = padding + col * (thumb_width + padding)
        cell_y = padding + row * (cell_height + padding)

        # Thumbnail is centered within the thumbnail area of the cell.
        thumb_area_x = cell_x
        thumb_area_y = cell_y

        try:
            with Image.open(image_path) as img:
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')

                img.thumbnail(thumb_size, Image.Resampling.LANCZOS)

                thumb_w, thumb_h = img.size
                offset_x = thumb_area_x + (thumb_width - thumb_w) // 2
                offset_y = thumb_area_y + (thumb_height - thumb_h) // 2

                if img.mode == 'L':
                    img = img.convert('RGB')
                contact_sheet.paste(img, (offset_x, offset_y))

        except Exception as e:
            print(f"Warning: Could not process '{image_path}': {e}")
            draw.rectangle(
                [thumb_area_x, thumb_area_y,
                 thumb_area_x + thumb_width, thumb_area_y + thumb_height],
                outline='red', width=2
            )
            draw.text(
                (thumb_area_x + 10, thumb_area_y + thumb_height // 2),
                "Error", fill='red', font=font
            )

        # --- Caption strip (only when labeling) ---
        if label and caption_height > 0:
            text = image_path.name

            # Truncate long filenames to fit the cell width.
            limit = label_max_chars
            if limit is None:
                # Rough but font-aware-ish heuristic: measure and shrink.
                limit = max(1, thumb_width // max(1, label_font_size // 2))
                # Better: measure actual pixel width and elide precisely.
            if limit is not None and len(text) > limit:
                text = text[: max(1, limit - 3)] + "..."

            # Precise elision by pixel width, in case the heuristic overshoots.
            while text and _text_width(draw, text, font) > thumb_width:
                # Drop a char, keep the ellipsis.
                core = text[:-3] if text.endswith("...") else text
                if len(core) <= 1:
                    text = core
                    break
                text = core[:-1] + "..."

            text_w = _text_width(draw, text, font)
            text_x = cell_x + (thumb_width - text_w) // 2
            text_y = cell_y + thumb_height + 3  # 3 px gap below thumbnail

            draw.text((text_x, text_y), text, fill='black', font=font)

    contact_sheet.save(output_path, quality=95)
    print(f"Contact sheet saved to '{output_path}' "
          f"({num_images} images, {columns}x{rows} grid, "
          f"labels={'on' if label else 'off'})")
    return True


def _text_width(draw, text, font):
    """Return the pixel width of `text` rendered with `font`."""
    if not text:
        return 0
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]
    except AttributeError:
        # Very old Pillow
        return draw.textsize(text, font=font)[0]