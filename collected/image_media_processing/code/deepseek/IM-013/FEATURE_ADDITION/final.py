import os
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont


def _load_font(size):
    """Try to load a TrueType font; fall back to the default bitmap font."""
    for candidate in (
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def build_contact_sheet(input_dir, output_path, thumb_size, columns, label=True):
    """
    Build a contact sheet by tiling all images from input_dir into a grid.

    Args:
        input_dir (str): Directory containing the images.
        output_path (str): Path to save the contact sheet image.
        thumb_size (tuple): (width, height) of each thumbnail in pixels.
        columns (int): Number of columns in the grid.
        label (bool): If True, draw each image's filename beneath its thumbnail.

    Returns:
        str: Path to the saved contact sheet.
    """
    if columns < 1:
        raise ValueError("columns must be >= 1")

    thumb_w, thumb_h = thumb_size
    if thumb_w < 1 or thumb_h < 1:
        raise ValueError("thumb_size dimensions must be >= 1")

    # Collect image files (sorted for deterministic ordering)
    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'}
    image_paths = sorted(
        p for p in Path(input_dir).iterdir()
        if p.is_file() and p.suffix.lower() in valid_exts
    )

    if not image_paths:
        raise ValueError(f"No image files found in {input_dir}")

    # Caption strip dimensions (only when labeling)
    caption_h = 0
    font = None
    if label:
        font = _load_font(max(10, thumb_h // 12))
        # Reserve ~18% of the thumbnail height for the caption strip
        caption_h = max(16, thumb_h // 6)

    cell_w = thumb_w
    cell_h = thumb_h + caption_h

    # Load and resize thumbnails, letterboxing to preserve aspect ratio
    thumbs = []  # list of (PIL.Image, caption_text)
    for path in image_paths:
        try:
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img)  # fix rotation metadata
                img = img.convert("RGB")
                fitted = ImageOps.pad(
                    img, (thumb_w, thumb_h),
                    method=Image.Resampling.LANCZOS,
                    color=(0, 0, 0),
                    centering=(0.5, 0.5),
                )
                thumbs.append((fitted, path.name))
        except Exception as e:
            print(f"Skipping {path}: {e}")

    if not thumbs:
        raise ValueError("No valid images could be loaded.")

    # Compute grid dimensions
    rows = (len(thumbs) + columns - 1) // columns
    sheet_w = cell_w * columns
    sheet_h = cell_h * rows

    # Build the contact sheet
    sheet = Image.new("RGB", (sheet_w, sheet_h), (0, 0, 0))
    draw = ImageDraw.Draw(sheet) if label else None

    for index, (thumb, name) in enumerate(thumbs):
        row, col = divmod(index, columns)
        x = col * cell_w
        y = row * cell_h

        # Paste thumbnail into the top portion of the cell
        sheet.paste(thumb, (x, y))

        # Draw caption beneath the thumbnail
        if label:
            cap_top = y + thumb_h
            cap_bottom = cap_top + caption_h
            draw.rectangle(
                [x, cap_top, x + cell_w - 1, cap_bottom - 1],
                fill=(20, 20, 20),
            )

            # Truncate filename to fit within the cell width
            text = name
            max_text_w = cell_w - 6
            bbox = draw.textbbox((0, 0), text, font=font)
            while (bbox[2] - bbox[0]) > max_text_w and len(text) > 1:
                text = text[:-2] + "…"
                bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            tx = x + (cell_w - text_w) // 2
            ty = cap_top + (caption_h - text_h) // 2 - bbox[1]
            draw.text((tx, ty), text, fill=(230, 230, 230), font=font)

    # Save
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    sheet.save(output_path)
    return output_path