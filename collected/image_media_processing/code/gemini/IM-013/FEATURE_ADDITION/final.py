import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def build_contact_sheet(
    input_dir,
    output_path,
    thumb_size=(150, 150),
    columns=4,
    label=True,
    caption_height=24,
    font_size=12,
    bg_color=(255, 255, 255),
    text_color=(0, 0, 0),
    padding=10
):
    """
    Tiles all images in a directory into a grid contact sheet with optional file labels.

    :param input_dir: Path to directory containing images.
    :param output_path: Destination path for the saved contact sheet.
    :param thumb_size: Tuple (width, height) reserved for the image thumbnail.
    :param columns: Number of columns in the grid.
    :param label: If True, draws the filename under each thumbnail cell.
    :param caption_height: Extra vertical height (in px) added to each cell when label=True.
    :param font_size: Size of the caption font.
    :param bg_color: RGB tuple for canvas background color.
    :param text_color: RGB tuple for caption text color.
    :param padding: Pixel spacing between cells and outer edges.
    """
    input_path = Path(input_dir)
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}
    
    # Filter valid images
    image_files = [
        f for f in sorted(input_path.iterdir())
        if f.is_file() and f.suffix.lower() in valid_extensions
    ]
    
    if not image_files:
        raise ValueError(f"No valid image files found in '{input_dir}'.")

    # Layout parameters
    num_images = len(image_files)
    rows = math.ceil(num_images / columns)
    thumb_w, thumb_h = thumb_size
    
    # Reserve extra vertical space for captions if label=True
    label_offset = caption_height if label else 0
    cell_h = thumb_h + label_offset

    # Compute overall sheet dimensions
    sheet_width = columns * thumb_w + (columns + 1) * padding
    sheet_height = rows * cell_h + (rows + 1) * padding

    # Create canvas and drawing context
    contact_sheet = Image.new("RGB", (sheet_width, sheet_height), color=bg_color)
    draw = ImageDraw.Draw(contact_sheet)

    # Load default font or fallback TTF
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    for index, img_file in enumerate(image_files):
        col = index % columns
        row = index // columns
        
        # Calculate cell top-left starting corner
        cell_x = padding + col * (thumb_w + padding)
        cell_y = padding + row * (cell_h + padding)

        try:
            with Image.open(img_file) as img:
                img = img.convert("RGB")
                img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                
                # Center thumbnail inside top image area of the cell
                img_x = cell_x + (thumb_w - img.width) // 2
                img_y = cell_y + (thumb_h - img.height) // 2
                contact_sheet.paste(img, (img_x, img_y))

        except Exception as e:
            print(f"Skipping corrupt image {img_file.name}: {e}")
            continue

        # Draw caption if enabled
        if label:
            filename = img_file.name
            
            # Truncate overly long text so it doesn't overflow cell bounds
            max_chars = max(5, thumb_w // (font_size // 2 or 1))
            if len(filename) > max_chars:
                filename = filename[: max_chars - 3] + "..."

            # Calculate centered position for label
            bbox = draw.textbbox((0, 0), filename, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            text_x = cell_x + (thumb_w - text_w) // 2
            text_y = cell_y + thumb_h + (label_offset - text_h) // 2

            draw.text((text_x, text_y), filename, fill=text_color, font=font)

    # Save output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    contact_sheet.save(output_file)
    print(f"Contact sheet saved to {output_path}")

# Example Usage
if __name__ == "__main__":
    build_contact_sheet(
        input_dir="./my_photos",
        output_path="./contact_sheet_labeled.jpg",
        thumb_size=(200, 200),
        columns=4,
        label=True,
        caption_height=30,
        font_size=12
    )