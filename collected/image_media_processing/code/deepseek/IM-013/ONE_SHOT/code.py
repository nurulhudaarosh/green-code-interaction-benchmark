from PIL import Image
import os
from pathlib import Path
import math

def build_contact_sheet(input_dir, output_path, thumb_size, columns):
    """
    Create a contact sheet by tiling all images from input_dir into a grid.
    
    Args:
        input_dir (str): Directory containing images
        output_path (str): Path where the contact sheet will be saved
        thumb_size (tuple): Size of each thumbnail as (width, height)
        columns (int): Number of columns in the grid
    
    Returns:
        str: Path to the created contact sheet
    """
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    # Get all image files from the directory
    image_files = []
    for file in sorted(os.listdir(input_dir)):
        file_path = os.path.join(input_dir, file)
        if os.path.isfile(file_path):
            ext = Path(file).suffix.lower()
            if ext in image_extensions:
                image_files.append(file_path)
    
    if not image_files:
        raise ValueError(f"No image files found in {input_dir}")
    
    thumb_width, thumb_height = thumb_size
    num_images = len(image_files)
    rows = math.ceil(num_images / columns)
    
    # Create the contact sheet canvas (white background)
    sheet_width = thumb_width * columns
    sheet_height = thumb_height * rows
    contact_sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
    
    # Place each thumbnail in the grid
    for index, image_path in enumerate(image_files):
        try:
            with Image.open(image_path) as img:
                # Convert to RGB (handles RGBA, palette, etc.)
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Resize maintaining aspect ratio, then center in cell
                img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                
                # Calculate position (centered in cell)
                col = index % columns
                row = index // columns
                cell_x = col * thumb_width
                cell_y = row * thumb_height
                paste_x = cell_x + (thumb_width - img.width) // 2
                paste_y = cell_y + (thumb_height - img.height) // 2
                
                contact_sheet.paste(img, (paste_x, paste_y))
        except Exception as e:
            print(f"Warning: Could not process {image_path}: {e}")
            continue
    
    # Save the contact sheet
    contact_sheet.save(output_path)
    return output_path


# Example usage
if __name__ == "__main__":
    build_contact_sheet(
        input_dir="./images",
        output_path="contact_sheet.jpg",
        thumb_size=(200, 200),
        columns=5
    )