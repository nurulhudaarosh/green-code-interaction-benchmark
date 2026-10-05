import os
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
        str: Path to the saved contact sheet.
    """
    input_dir = Path(input_dir)
    thumb_w, thumb_h = thumb_size

    # Gather image files (sorted for reproducibility)
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    image_paths = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in valid_exts
    )

    if not image_paths:
        raise ValueError(f"No images found in {input_dir}")

    # Compute grid dimensions
    columns = max(1, int(columns))
    rows = (len(image_paths) + columns - 1) // columns

    sheet_w = columns * thumb_w
    sheet_h = rows * thumb_h

    # Create blank canvas (white background)
    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(255, 255, 255))

    for idx, img_path in enumerate(image_paths):
        row = idx // columns
        col = idx % columns
        x = col * thumb_w
        y = row * thumb_h

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
                sheet.paste(tile, (x, y))
        except Exception as e:
            print(f"Skipping {img_path.name}: {e}")

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Choose format based on extension
    ext = output_path.suffix.lower()
    save_kwargs = {}
    if ext in (".jpg", ".jpeg"):
        save_kwargs["quality"] = 90
    sheet.save(output_path, **save_kwargs)
    return str(output_path)


# Example usage
if __name__ == "__main__":
    build_contact_sheet(
        input_dir="images",
        output_path="contact_sheet.jpg",
        thumb_size=(200, 200),
        columns=5,
    )