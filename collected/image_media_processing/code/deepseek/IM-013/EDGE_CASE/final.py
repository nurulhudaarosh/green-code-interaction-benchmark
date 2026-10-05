import os
import math
from pathlib import Path
from PIL import Image, ImageOps

def build_contact_sheet(input_dir, output_path, thumb_size, columns):
    """
    Create a contact sheet by tiling all images from input_dir into a grid.
    
    Args:
        input_dir (str): Directory containing the images.
        output_path (str): Path to save the output contact sheet image.
        thumb_size (tuple): (width, height) of each thumbnail in pixels.
        columns (int): Number of columns in the grid.
    
    Returns:
        tuple: (rows, columns) used in the grid. Returns (0, columns) when
               no valid images are found.
    """
    input_dir = Path(input_dir)
    thumb_w, thumb_h = thumb_size
    columns = max(1, int(columns))

    # Gather image files (sorted for reproducibility)
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    image_paths = []
    if input_dir.is_dir():
        image_paths = sorted(
            p for p in input_dir.iterdir()
            if p.is_file() and p.suffix.lower() in valid_exts
        )

    # --- Edge case: no valid images -------------------------------------
    if not image_paths:
        # Use a 1-pixel-high strip wide enough to remain a valid image.
        sheet_w = columns * thumb_w
        sheet_h = 1
        sheet = Image.new("RGB", (sheet_w, sheet_h), color=(255, 255, 255))

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        ext = output_path.suffix.lower()
        save_kwargs = {}
        if ext in (".jpg", ".jpeg"):
            save_kwargs["quality"] = 90
        sheet.save(output_path, **save_kwargs)
        return (0, columns)
    # --------------------------------------------------------------------

    # Compute grid dimensions
    rows = math.ceil(len(image_paths) / columns)
    sheet_w = columns * thumb_w
    sheet_h = rows * thumb_h

    # Create blank canvas (white background)
    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(255, 255, 255))

    placed = 0
    for img_path in image_paths:
        try:
            with Image.open(img_path) as im:
                # Preserve transparency by compositing on white
                if im.mode in ("RGBA", "LA", "P"):
                    im = im.convert("RGBA")
                    bg = Image.new("RGB", im.size, (255, 255, 255))
                    bg.paste(im, mask=im.split()[-1])
                    im = bg
                else:
                    im = im.convert("RGB")

                # Resize preserving aspect ratio, then pad to thumb_size
                thumb = ImageOps.contain(im, (thumb_w, thumb_h), Image.LANCZOS)
                tile = Image.new("RGB", (thumb_w, thumb_h), (255, 255, 255))
                offset = (
                    (thumb_w - thumb.width) // 2,
                    (thumb_h - thumb.height) // 2,
                )
                tile.paste(thumb, offset)

                row = placed // columns
                col = placed % columns
                sheet.paste(tile, (col * thumb_w, row * thumb_h))
                placed += 1
        except Exception as e:
            print(f"Skipping {img_path.name}: {e}")

    # If every image failed to decode, fall back to the empty-sheet behavior.
    if placed == 0:
        sheet = Image.new("RGB", (columns * thumb_w, 1), color=(255, 255, 255))
        rows = 0

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ext = output_path.suffix.lower()
    save_kwargs = {}
    if ext in (".jpg", ".jpeg"):
        save_kwargs["quality"] = 90
    sheet.save(output_path, **save_kwargs)
    return (rows, columns)