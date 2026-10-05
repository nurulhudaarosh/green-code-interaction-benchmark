import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

def build_contact_sheet(input_dir, output_path, thumb_size=(200, 200), columns=4):
    """
    Create a contact sheet by tiling all images from input_dir into a grid.

    Args:
        input_dir (str): Directory containing images
        output_path (str): Path where the contact sheet will be saved
        thumb_size (tuple): Size of each thumbnail (width, height)
        columns (int): Number of columns in the grid

    Returns:
        bool: True if successful, False otherwise
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

    # FIX: ceiling division using integer arithmetic only.
    # (n + columns - 1) // columns == ceil(n / columns) for positive ints.
    # Using n // columns would drop the trailing partial row when
    # n is not an exact multiple of columns.
    rows = (num_images + columns - 1) // columns

    padding = 10
    label_height = 20

    thumb_width, thumb_height = thumb_size
    canvas_width = (columns * thumb_width) + ((columns + 1) * padding)
    canvas_height = (rows * (thumb_height + label_height)) + ((rows + 1) * padding)

    contact_sheet = Image.new('RGB', (canvas_width, canvas_height), 'white')
    draw = ImageDraw.Draw(contact_sheet)

    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except (OSError, IOError):
        font = ImageFont.load_default()

    for idx, image_path in enumerate(image_files):
        row = idx // columns
        col = idx % columns

        x = padding + col * (thumb_width + padding)
        y = padding + row * (thumb_height + label_height + padding)

        try:
            with Image.open(image_path) as img:
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')

                img.thumbnail(thumb_size, Image.Resampling.LANCZOS)

                thumb_w, thumb_h = img.size
                offset_x = x + (thumb_width - thumb_w) // 2
                offset_y = y + (thumb_height - thumb_h) // 2

                if img.mode == 'L':
                    img = img.convert('RGB')
                contact_sheet.paste(img, (offset_x, offset_y))

                if label_height > 0:
                    label = image_path.name
                    max_chars = thumb_width // 7
                    if len(label) > max_chars:
                        label = label[:max_chars - 3] + "..."

                    bbox = draw.textbbox((0, 0), label, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_x = x + (thumb_width - text_width) // 2
                    text_y = y + thumb_height + 2

                    draw.text((text_x, text_y), label, fill='black', font=font)

        except Exception as e:
            print(f"Warning: Could not process '{image_path}': {e}")
            draw.rectangle(
                [x, y, x + thumb_width, y + thumb_height],
                outline='red', width=2
            )
            draw.text(
                (x + 10, y + thumb_height // 2), "Error",
                fill='red', font=font
            )

    contact_sheet.save(output_path, quality=95)
    print(f"Contact sheet saved to '{output_path}' "
          f"({num_images} images, {columns}x{rows} grid)")
    return True