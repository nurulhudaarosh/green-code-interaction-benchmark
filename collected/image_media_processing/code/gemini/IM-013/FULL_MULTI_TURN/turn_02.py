import os
from PIL import Image


def build_contact_sheet(
    input_dir: str,
    output_path: str,
    thumb_size: tuple[int, int] = (150, 150),
    columns: int = 4,
    padding: int = 10,
    bg_color: str | tuple[int, int, int] = "white",
):
    """Tiles all images from `input_dir` into a grid contact sheet.

    Args:
        input_dir: Directory containing input images.
        output_path: File path where the contact sheet image will be saved.
        thumb_size: (width, height) bounding box for each thumbnail cell.
        columns: Fixed number of columns in the grid.
        padding: Pixel spacing between thumbnails and outer borders.
        bg_color: Background color for the contact sheet.
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

    cell_w, cell_h = thumb_size
    num_images = len(image_paths)

    # 2. Compute rows using integer ceiling division to ensure trailing partial rows are retained
    rows = (num_images + columns - 1) // columns

    # Calculate canvas dimensions including padding
    canvas_w = columns * cell_w + (columns + 1) * padding
    canvas_h = rows * cell_h + (rows + 1) * padding

    contact_sheet = Image.new("RGB", (canvas_w, canvas_h), color=bg_color)

    # 3. Process each image and paste into grid position
    for idx, img_path in enumerate(image_paths):
        row = idx // columns
        col = idx % columns

        # Calculate top-left pixel position for the grid cell
        x = padding + col * (cell_w + padding)
        y = padding + row * (cell_h + padding)

        try:
            with Image.open(img_path) as img:
                # Convert RGBA/Palette images to RGB for background blending
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGBA")
                    bg = Image.new("RGBA", img.size, bg_color)
                    img = Image.alpha_composite(bg, img).convert("RGB")
                else:
                    img = img.convert("RGB")

                # Resize image while preserving aspect ratio inside thumb_size
                img.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)

                # Center the thumbnail inside the cell box
                offset_x = x + (cell_w - img.width) // 2
                offset_y = y + (cell_h - img.height) // 2

                contact_sheet.paste(img, (offset_x, offset_y))

        except Exception as e:
            print(f"Warning: Skipping unreadable image '{img_path}': {e}")

    # 4. Save final contact sheet
    contact_sheet.save(output_path)
    print(
        f"Successfully created contact sheet with {num_images} images at '{output_path}'"
    )