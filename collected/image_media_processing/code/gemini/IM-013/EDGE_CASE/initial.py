import math
import os
from PIL import Image

def build_contact_sheet(input_dir: str, output_path: str, thumb_size: tuple[int, int], columns: int, bg_color: tuple[int, int, int] = (255, 255, 255)):
    """
    Tiles all images in a directory into a grid contact sheet.

    :param input_dir: Path to directory containing images.
    :param output_path: Output file path for the contact sheet (e.g., 'contact_sheet.jpg').
    :param thumb_size: Tuple (width, height) specifying thumbnail dimensions.
    :param columns: Number of columns in the grid.
    :param bg_color: RGB background color tuple (default is white).
    """
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff')
    
    # 1. Gather all valid image file paths
    image_paths = [
        os.path.join(input_dir, f) for f in sorted(os.listdir(input_dir))
        if os.path.isfile(os.path.join(input_dir, f)) and f.lower().endswith(valid_extensions)
    ]
    
    if not image_paths:
        raise ValueError(f"No valid images found in directory: {input_dir}")

    # 2. Calculate grid geometry
    thumb_w, thumb_h = thumb_size
    total_images = len(image_paths)
    rows = math.ceil(total_images / columns)
    
    sheet_width = columns * thumb_w
    sheet_height = rows * thumb_h

    # 3. Create canvas image
    contact_sheet = Image.new('RGB', (sheet_width, sheet_height), color=bg_color)

    # 4. Process and paste each image
    for index, path in enumerate(image_paths):
        col = index % columns
        row = index // columns
        
        x = col * thumb_w
        y = row * thumb_h

        try:
            with Image.open(path) as img:
                # Convert RGBA/Palette modes to RGB before resizing
                if img.mode in ('RGBA', 'P', 'LA'):
                    img = img.convert('RGB')
                
                # Resize image while preserving aspect ratio and cropping to fit thumbnail box
                # (Use Image.LANCZOS for high quality downscaling)
                thumb = ImageOps.fit(img, thumb_size, Image.Resampling.LANCZOS)
                
                # Paste thumbnail into grid position
                contact_sheet.paste(thumb, (x, y))
        except Exception as e:
            print(f"Warning: Skipping unreadable image '{path}': {e}")

    # 5. Save final contact sheet
    contact_sheet.save(output_path)
    print(f"Successfully saved contact sheet ({total_images} images, {columns}x{rows} grid) to '{output_path}'.")