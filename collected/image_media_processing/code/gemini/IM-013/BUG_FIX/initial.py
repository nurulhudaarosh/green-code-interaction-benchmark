import os
from PIL import Image, ImageOps

def build_contact_sheet(input_dir: str, output_path: str, thumb_size: tuple[int, int], columns: int, padding: int = 10, bg_color: str = "white") -> None:
    """
    Tiles all images in a directory into a grid contact sheet.

    :param input_dir: Path to directory containing source images.
    :param output_path: Path where the resulting contact sheet will be saved.
    :param thumb_size: Tuple (width, height) specifying max size for each thumbnail cell.
    :param columns: Number of columns in the grid.
    :param padding: Pixel spacing between thumbnails and outer borders.
    :param bg_color: Background color of the contact sheet (e.g., 'white', 'black', '#F0F0F0').
    """
    # Supported image extensions
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
    
    # Gather image file paths
    image_paths = [
        os.path.join(input_dir, f) for f in sorted(os.listdir(input_dir))
        if f.lower().endswith(valid_extensions)
    ]
    
    if not image_paths:
        raise ValueError(f"No supported images found in '{input_dir}'.")

    cell_width, cell_height = thumb_size
    total_images = len(image_paths)
    
    # Calculate required rows
    rows = (total_images + columns - 1) // columns
    
    # Calculate contact sheet canvas dimensions
    canvas_width = columns * cell_width + (columns + 1) * padding
    canvas_height = rows * cell_height + (rows + 1) * padding
    
    # Create canvas
    contact_sheet = Image.new("RGB", (canvas_width, canvas_height), color=bg_color)
    
    for idx, path in enumerate(image_paths):
        row = idx // columns
        col = idx % columns
        
        # Calculate top-left position for current thumbnail cell
        x = padding + col * (cell_width + padding)
        y = padding + row * (cell_height + padding)
        
        try:
            with Image.open(path) as img:
                # Correct image orientation based on EXIF data if present
                img = ImageOps.exif_transpose(img)
                img = img.convert("RGBA")  # Handle potential transparency
                
                # Resize image while preserving aspect ratio
                img.thumbnail((cell_width, cell_height), Image.Resampling.LANCZOS)
                
                # Center image within the allocated cell box
                offset_x = x + (cell_width - img.width) // 2
                offset_y = y + (cell_height - img.height) // 2
                
                # Create a temporary RGB background for alpha blending if image has transparency
                cell_bg = Image.new("RGBA", img.size, bg_color)
                composite = Image.alpha_composite(cell_bg, img).convert("RGB")
                
                contact_sheet.paste(composite, (offset_x, offset_y))
        except Exception as e:
            print(f"Warning: Could not process '{path}': {e}")
            
    # Save output contact sheet
    contact_sheet.save(output_path)
    print(f"Contact sheet saved successfully to '{output_path}'.")


# Example Usage:
if __name__ == "__main__":
    # Create contact sheet with 4 columns and 200x200 pixel cells
    build_contact_sheet(
        input_dir="./images",
        output_path="./contact_sheet.jpg",
        thumb_size=(200, 200),
        columns=4,
        padding=15,
        bg_color="white"
    )