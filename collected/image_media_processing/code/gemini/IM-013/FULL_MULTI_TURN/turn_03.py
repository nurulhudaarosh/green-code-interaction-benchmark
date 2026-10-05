import os
from PIL import Image, ImageDraw, ImageFont


def build_contact_sheet(
    input_dir: str,
    output_path: str,
    thumb_size: tuple[int, int] = (150, 150),
    columns: int = 4,
    padding: int = 10,
    bg_color: str | tuple[int, int, int] = "white",
    label: bool = False,
    label_height: int = 24,
    text_color: str | tuple[int, int, int] = "black",
):
    """Tiles all images from `input_dir` into a grid contact sheet.

    Args:
        input_dir: Directory containing input images.
        output_path: File path where the contact sheet image will be saved.
        thumb_size: (width, height) bounding box for each thumbnail image.
        columns: Fixed number of columns in the grid.
        padding: Pixel spacing between cells and outer borders.
        bg_color: Background color for the contact sheet.
        label: If True, draws filename captions beneath each thumbnail.
        label_height: Additional pixel height reserved for the text strip when label=True.
        text_color: Font color for image captions.
    """
    valid_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp",
        ".tiff",
        ".gif",
    )

    # 1. Collect all image paths from input directory
    image_paths = [
        os.path.join(input_dir, f)
        for f in sorted(os.listdir(input_dir))
        if f.lower().endswith(valid_extensions)
    ]

    if not image_paths:
        raise ValueError(f"No valid images found in directory: '{input_dir}'")

    cell_w, thumb_h = thumb_size
    # Adjust total cell height if captions are enabled
    cell_h = thumb_h + (label_height if label else 0)

    num_images = len(image_paths)
    rows = (num_images + columns - 1) // columns

    # 2. Compute canvas dimensions including padding
    canvas_w = columns * cell_w + (columns + 1) * padding
    canvas_h = rows * cell_h + (rows + 1) * padding

    contact_sheet = Image.new("RGB", (canvas_w, canvas_h), color=bg_color)
    draw = ImageDraw.Draw(contact_sheet) if label else None
    font = ImageFont.load_default()

    # Helper function to truncate long text to fit cell width
    def fit_text(text: str, max_w: int, draw_obj, font_obj) -> str:
        bbox = draw_obj.textbbox((0, 0), text, font=font_obj)
        if (bbox[2] - bbox[0]) <= max_w:
            return text

        ellipsis = "..."
        for i in range(len(text) - 1, 0, -1):
            truncated = text[:i] + ellipsis
            bbox = draw_obj.textbbox((0, 0), truncated, font=font_obj)
            if (bbox[2] - bbox[0]) <= max_w:
                return truncated
        return ellipsis

    # 3. Process each image and paste into grid position
    for idx, img_path in enumerate(image_paths):
        row = idx // columns
        col = idx % columns

        # Cell top-left coordinate
        cell_x = padding + col * (cell_w + padding)
        cell_y = padding + row * (cell_h + padding)

        try:
            with Image.open(img_path) as img:
                # Convert RGBA/Palette images to RGB
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGBA")
                    bg = Image.new("RGBA", img.size, bg_color)
                    img = Image.alpha_composite(bg, img).convert("RGB")
                else:
                    img = img.convert("RGB")

                # Resize image while preserving aspect ratio inside thumb area
                img.thumbnail((cell_w, thumb_h), Image.Resampling.LANCZOS)

                # Center thumbnail horizontally and vertically within its upper thumb area
                offset_x = cell_x + (cell_w - img.width) // 2
                offset_y = cell_y + (thumb_h - img.height) // 2

                contact_sheet.paste(img, (offset_x, offset_y))

                # 4. Render label beneath thumbnail
                if label:
                    filename = os.path.basename(img_path)
                    caption = fit_text(filename, cell_w, draw, font)

                    # Compute text dimensions for precise centering
                    text_bbox = draw.textbbox((0, 0), caption, font=font)
                    text_w = text_bbox[2] - text_bbox[0]
                    text_h = text_bbox[3] - text_bbox[1]

                    # Position text centered in the caption strip
                    text_x = cell_x + (cell_w - text_w) // 2
                    text_y = cell_y + thumb_h + (label_height - text_h) // 2

                    draw.text(
                        (text_x, text_y),
                        caption,
                        fill=text_color,
                        font=font,
                    )

        except Exception as e:
            print(f"Warning: Skipping unreadable image '{img_path}': {e}")

    # 5. Save final contact sheet
    contact_sheet.save(output_path)
    print(
        f"Successfully created contact sheet with {num_images} images at '{output_path}'"
    )


# --- Example Usage ---
if __name__ == "__main__":
    build_contact_sheet(
        input_dir="./photos",
        output_path="labeled_contact_sheet.jpg",
        thumb_size=(150, 150),
        columns=4,
        padding=10,
        bg_color="white",
        label=True,  # Enables filename captions beneath images
        label_height=20,  # 20px caption strip
        text_color="black",
    )