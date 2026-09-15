from pathlib import Path
from PIL import Image

def convert_format(input_dir: str | Path, output_dir: str | Path, target_format: str, bg_color: tuple = (255, 255, 255)) -> None:
    """
    Converts all images in input_dir to target_format ('PNG' or 'JPEG'/'JPG').
    Safely handles transparent images when saving to formats without alpha support.
    
    :param input_dir: Path to directory containing source images.
    :param output_dir: Path to save converted images.
    :param target_format: Target format string ('PNG', 'JPEG', 'JPG').
    :param bg_color: RGB tuple to use for filling transparency when converting to JPEG.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Normalize target format
    fmt = target_format.upper()
    if fmt == 'JPG':
        fmt = 'JPEG'
        
    if fmt not in {'PNG', 'JPEG'}:
        raise ValueError("target_format must be 'PNG' or 'JPEG' (or 'JPG').")
        
    # Extension map for output files
    ext = '.jpg' if fmt == 'JPEG' else '.png'
    
    # Ensure destination directory exists
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Valid file extensions to attempt reading
    valid_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff', '.tif'}

    for file in input_path.iterdir():
        if file.is_file() and file.suffix.lower() in valid_exts:
            try:
                with Image.open(file) as img:
                    # Prepare image for format requirement
                    if fmt == 'JPEG':
                        # Handle images with alpha channels (RGBA, LA, P with transparency)
                        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                            # Convert to RGBA first to obtain proper alpha mask
                            rgba_img = img.convert('RGBA')
                            # Create a solid background image
                            background = Image.new('RGB', rgba_img.size, bg_color)
                            # Composite original image over background using alpha channel as mask
                            background.paste(rgba_img, mask=rgba_img.split()[3])
                            converted_img = background
                        else:
                            converted_img = img.convert('RGB')
                    else:
                        # For PNG, retain image mode (or convert to RGBA/RGB as needed)
                        converted_img = img

                    # Save converted file
                    out_file = output_path / f"{file.stem}{ext}"
                    converted_img.save(out_file, format=fmt)
                    print(f"Converted: {file.name} -> {out_file.name}")
                    
            except Exception as e:
                print(f"Failed to convert {file.name}: {e}")

# Example usage:
# convert_format("source_images", "converted_images", "JPEG")