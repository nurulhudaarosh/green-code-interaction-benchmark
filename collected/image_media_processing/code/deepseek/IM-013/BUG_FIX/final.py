from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

def build_contact_sheet(input_dir, output_path, thumb_size=(200, 200), columns=4):
    """
    Tile all images from input_dir into a grid contact sheet.

    Args:
        input_dir: Directory containing source images.
        output_path: Path to save the resulting contact sheet.
        thumb_size: (width, height) tuple for each thumbnail. If a single int
                    is given, it's used for both dimensions.
        columns: Fixed number of columns in the grid.

    Returns:
        Path to the saved contact sheet.
    """
    if isinstance(thumb_size, int):
        thumb_size = (thumb_size, thumb_size)
    tw, th = thumb_size

    input_dir = Path(input_dir)
    output_path = Path(output_path)

    # Collect image files (common formats, sorted for reproducibility)
    extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    image_paths = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in extensions
    )

    if not image_paths:
        raise ValueError(f"No images found in {input_dir}")

    # Grid dimensions
    cols = max(1, int(columns))
    n = len(image_paths)

    # Ceiling division: ensures the trailing partial row is included.
    # Equivalent to math.ceil(n / cols), but avoids float precision issues.
    rows = -(-n // cols)          # or: rows = (n + cols - 1) // cols

    # Optional padding between cells and a label strip under each thumbnail
    pad = 4
    label_height = 14

    cell_w = tw + pad * 2
    cell_h = th + pad * 2 + label_height

    sheet_w = cols * cell_w
    sheet_h = rows * cell_h

    sheet = Image.new('RGB', (sheet_w, sheet_h), (30, 30, 30))
    draw = ImageDraw.Draw(sheet)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for idx, img_path in enumerate(image_paths):
        r, c = divmod(idx, cols)
        x = c * cell_w + pad
        y = r * cell_h + pad

        try:
            with Image.open(img_path) as im:
                im = im.convert('RGB')
                im.thumbnail((tw, th), Image.LANCZOS)
                off_x = x + (tw - im.width) // 2
                off_y = y + (th - im.height) // 2
                sheet.paste(im, (off_x, off_y))
        except Exception as e:
            draw.rectangle([x, y, x + tw, y + th], outline=(200, 0, 0))
            draw.text((x + 4, y + 4), "ERR", fill=(255, 80, 80), font=font)
            print(f"Failed to load {img_path}: {e}")

        if font is not None:
            label = img_path.name
            max_chars = max(1, cell_w // 6)
            if len(label) > max_chars:
                label = label[:max_chars - 1] + '…'
            draw.text((x, y + th + 2), label, fill=(220, 220, 220), font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)
    return output_path


if __name__ == "__main__":
    build_contact_sheet(
        input_dir="images",
        output_path="contact_sheet.jpg",
        thumb_size=(200, 200),
        columns=5,
    )