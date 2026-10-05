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
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    # Get all image files in the directory
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist")
    
    image_files = []
    for file in sorted(input_path.iterdir()):
        if file.is_file() and file.suffix.lower() in image_extensions:
            image_files.append(file)
    
    if not image_files:
        raise ValueError(f"No image files found in '{input_dir}'")
    
    # Calculate grid dimensions
    num_images = len(image_files)
    rows = math.ceil(num_images / columns)
    
    # Calculate spacing and padding
    padding = 10  # Padding between images and around edges
    label_height = 20  # Height for filename labels (set to 0 to disable labels)
    
    # Calculate total canvas size
    thumb_width, thumb_height = thumb_size
    canvas_width = (columns * thumb_width) + ((columns + 1) * padding)
    canvas_height = (rows * (thumb_height + label_height)) + ((rows + 1) * padding)
    
    # Create the contact sheet canvas (white background)
    contact_sheet = Image.new('RGB', (canvas_width, canvas_height), 'white')
    draw = ImageDraw.Draw(contact_sheet)
    
    # Try to load a font for labels (falls back to default if not available)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except (OSError, IOError):
        font = ImageFont.load_default()
    
    # Process each image
    for idx, image_path in enumerate(image_files):
        try:
            # Calculate grid position
            row = idx // columns
            col = idx % columns
            
            # Calculate pixel position
            x = padding + col * (thumb_width + padding)
            y = padding + row * (thumb_height + label_height + padding)
            
            # Open and resize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Create thumbnail maintaining aspect ratio
                img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                
                # Center the thumbnail in its cell
                thumb_w, thumb_h = img.size
                offset_x = x + (thumb_width - thumb_w) // 2
                offset_y = y + (thumb_height - thumb_h) // 2
                
                # Paste the thumbnail
                if img.mode == 'L':
                    img = img.convert('RGB')
                contact_sheet.paste(img, (offset_x, offset_y))
                
                # Add filename label if enabled
                if label_height > 0:
                    label = image_path.name
                    # Truncate long filenames
                    max_chars = thumb_width // 7  # Rough estimate
                    if len(label) > max_chars:
                        label = label[:max_chars-3] + "..."
                    
                    # Center the label text
                    bbox = draw.textbbox((0, 0), label, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_x = x + (thumb_width - text_width) // 2
                    text_y = y + thumb_height + 2
                    
                    draw.text((text_x, text_y), label, fill='black', font=font)
                    
        except Exception as e:
            print(f"Warning: Could not process '{image_path}': {e}")
            # Draw an error placeholder
            row = idx // columns
            col = idx % columns
            x = padding + col * (thumb_width + padding)
            y = padding + row * (thumb_height + label_height + padding)
            
            draw.rectangle([x, y, x + thumb_width, y + thumb_height], 
                          outline='red', width=2)
            draw.text((x + 10, y + thumb_height // 2), "Error", 
                     fill='red', font=font)
    
    # Save the contact sheet
    contact_sheet.save(output_path, quality=95)
    print(f"Contact sheet saved to '{output_path}' ({num_images} images, {columns}x{rows} grid)")
    return True


# Example usage
if __name__ == "__main__":
    # Basic usage
    build_contact_sheet(
        input_dir="path/to/images",
        output_path="contact_sheet.jpg",
        thumb_size=(200, 200),
        columns=4
    )
    
    # With custom settings
    build_contact_sheet(
        input_dir="./photos",
        output_path="./output/contact_sheet.png",
        thumb_size=(150, 150),
        columns=6
    )