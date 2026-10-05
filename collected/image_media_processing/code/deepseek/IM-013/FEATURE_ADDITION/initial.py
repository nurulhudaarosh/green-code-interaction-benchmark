import os
from pathlib import Path
from PIL import Image, ImageOps

def build_contact_sheet(input_dir, output_path, thumb_size, columns):
    """
    Build a contact sheet by tiling all images from input_dir into a grid.
    
    Args:
        input_dir (str): Directory containing the images.
        output_path (str): Path to save the contact sheet image.
        thumb_size (tuple): (width, height) of each thumbnail in pixels.
        columns (int): Number of columns in the grid.
    
    Returns:
        str: Path to the saved contact sheet.
    """
    if columns < 1:
        raise ValueError("columns must be >= 1")
    
    thumb_w, thumb_h = thumb_size
    if thumb_w < 1 or thumb_h < 1:
        raise ValueError("thumb_size dimensions must be >= 1")
    
    # Collect image files (sorted for deterministic ordering)
    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'}
    image_paths = sorted(
        p for p in Path(input_dir).iterdir()
        if p.is_file() and p.suffix.lower() in valid_exts
    )
    
    if not image_paths:
        raise ValueError(f"No image files found in {input_dir}")
    
    # Load and resize thumbnails, letterboxing to preserve aspect ratio
    thumbs = []
    for path in image_paths:
        try:
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img)  # fix rotation metadata
                img = img.convert("RGB")
                fitted = ImageOps.pad(
                    img, (thumb_w, thumb_h),
                    method=Image.Resampling.LANCZOS,
                    color=(0, 0, 0),
                    centering=(0.5, 0.5),
                )
                thumbs.append(fitted)
        except Exception as e:
            print(f"Skipping {path}: {e}")
    
    if not thumbs:
        raise ValueError("No valid images could be loaded.")
    
    # Compute grid dimensions
    rows = (len(thumbs) + columns - 1) // columns
    sheet_w = thumb_w * columns
    sheet_h = thumb_h * rows
    
    # Build the contact sheet
    sheet = Image.new("RGB", (sheet_w, sheet_h), (0, 0, 0))
    for index, thumb in enumerate(thumbs):
        row, col = divmod(index, columns)
        sheet.paste(thumb, (col * thumb_w, row * thumb_h))
    
    # Save
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    sheet.save(output_path)
    return output_path