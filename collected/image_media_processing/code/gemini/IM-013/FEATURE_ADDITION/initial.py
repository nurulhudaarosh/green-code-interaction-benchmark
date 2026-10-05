import math
from pathlib import Path
from PIL import Image

def build_contact_sheet(input_dir, output_path, thumb_size=(150, 150), columns=4, bg_color=(255, 255, 255), padding=10):
    """
    Tiles all images in a directory into a grid contact sheet.

    :param input_dir: Path to directory containing images.
    :param output_path: Destination path for the saved contact sheet.
    :param thumb_size: Tuple (width, height) for each thumbnail.
    :param columns: Number of columns in the grid.
    :param bg_color: RGB tuple for background color (default is white).
    :param padding: Pixel spacing between thumbnails and outer edges.
    """
    input_path = Path(input_dir)
    
    # Supported image extensions
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}
    
    # Find all matching image files
    image_files = [
        f for f in sorted(input_path.iterdir())
        if f.is_file() and f.suffix.lower() in valid_extensions
    ]
    
    if not image_files:
        raise ValueError(f"No valid image files found in '{input_dir}'.")

    # Calculate grid layout
    num_images = len(image_files)
    rows = math.ceil(num_images / columns)
    
    thumb_w, thumb_h = thumb_size
    
    # Calculate total dimensions of the contact sheet
    sheet_width = columns * thumb_w + (columns + 1) * padding
    sheet_height = rows * thumb_h + (rows + 1) * padding
    
    # Create the background canvas
    contact_sheet = Image.new("RGB", (sheet_width, sheet_height), color=bg_color)
    
    # Process and tile each image
    for index, img_file in enumerate(image_files):
        try:
            with Image.open(img_file) as img:
                # Convert RGBA / P images to RGB for clean saving
                img = img.convert("RGB")
                
                # Resize keeping aspect ratio, fitted within thumb_size
                img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                
                # Center thumbnail inside the thumbnail box frame
                col = index % columns
                row = index // columns
                
                x_offset = padding + col * (thumb_w + padding) + (thumb_w - img.width) // 2
                y_offset = padding + row * (thumb_h + padding) + (thumb_h - img.height) // 2
                
                # Paste thumbnail onto canvas
                contact_sheet.paste(img, (x_offset, y_offset))
                
        except Exception as e:
            print(f"Skipping corrupt or unreadable image {img_file.name}: {e}")

    # Ensure output directory exists and save
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    contact_sheet.save(output_file)
    print(f"Contact sheet saved to {output_path}")

# Example Usage:
if __name__ == "__main__":
    build_contact_sheet(
        input_dir="./my_photos",
        output_path="./contact_sheet.jpg",
        thumb_size=(200, 200),
        columns=5,
        padding=15
    )