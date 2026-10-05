import os
from PIL import Image, ImageOps


def build_contact_sheet(
    input_dir: str,
    output_path: str,
    thumb_size: tuple[int, int] = (150, 150),
    columns: int = 5,
    bg_color: tuple[int, int, int] = (255, 255, 255),
    padding: int = 10,
) -> None:
    """Builds a contact sheet grid from images in a directory.

    Args:
        input_dir (str): Path to the folder containing input images.
        output_path (str): Destination file path for the output contact sheet.
        thumb_size (tuple): Width and height of individual thumbnails (width,
          height).
        columns (int): Number of image columns in the grid.
        bg_color (tuple): Background color RGB tuple. Defaults to white (255,
          255, 255).
        padding (int): Pixel padding between thumbnails and around borders.
    """
    # Supported image extensions
    valid_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp",
        ".tiff",
        ".gif",
    )

    # Gather image file paths
    image_paths = [
        os.path.join(input_dir, filename)
        for filename in sorted(os.listdir(input_dir))
        if filename.lower().endswith(valid_extensions)
    ]

    if not image_paths:
        print(f"No valid images found in {input_dir}")
        return

    num_images = len(image_paths)

    # Calculate grid rows
    rows = (num_images + columns - 1) // columns

    thumb_w, thumb_h = thumb_size

    # Calculate canvas dimensions taking padding into account
    canvas_w = columns * thumb_w + (columns + 1) * padding
    canvas_h = rows * thumb_h + (rows + 1) * padding

    # Create the background canvas
    contact_sheet = Image.new("RGB", (canvas_w, canvas_h), color=bg_color)

    # Process and place each image
    for index, img_path in enumerate(image_paths):
        col = index % columns
        row = index // columns

        # Compute position (x, y) for current thumbnail
        x = padding + col * (thumb_w + padding)
        y = padding + row * (thumb_h + padding)

        try:
            with Image.open(img_path) as img:
                # Convert RGBA/Palette images to RGB
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Resize and center-crop image to exactly fit thumb_size
                thumb = ImageOps.fit(
                    img, thumb_size, method=Image.Resampling.LANCZOS
                )

                # Paste thumbnail into grid canvas
                contact_sheet.paste(thumb, (x, y))

        except Exception as e:
            print(f"Skipping corrupt or unreadable image '{img_path}': {e}")

    # Ensure target output folder exists and save result
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    contact_sheet.save(output_path)
    print(
        f"Successfully created contact sheet with {num_images} images: {output_path}"
    )