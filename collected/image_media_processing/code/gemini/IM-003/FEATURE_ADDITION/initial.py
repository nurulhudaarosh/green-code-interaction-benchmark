from pathlib import Path
from PIL import Image

def convert_format(input_dir: str | Path, output_dir: str | Path, target_format: str) -> None:
    """
    Converts all supported images in input_dir to the target_format and saves them in output_dir.
    
    :param input_dir: Path to the directory containing input images.
    :param output_dir: Path to the directory where converted images will be saved.
    :param target_format: Target format ('PNG', 'JPEG', or 'JPG').
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    fmt = target_format.upper().strip('.')
    if fmt == 'JPG':
        fmt = 'JPEG'
        
    if fmt not in {'PNG', 'JPEG'}:
        raise ValueError("target_format must be either 'PNG' or 'JPEG' (or 'JPG').")

    output_path.mkdir(parents=True, exist_ok=True)
    
    # Supported input extensions
    valid_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif'}
    
    for file_path in input_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_exts:
            try:
                with Image.open(file_path) as img:
                    output_filename = f"{file_path.stem}.{fmt.lower()}"
                    destination = output_path / output_filename
                    
                    if fmt == 'JPEG':
                        # JPEG does not support alpha channels.
                        # Flatten RGBA / LA / P images onto a white background.
                        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                            # Convert to RGBA first to ensure standard alpha channel processing
                            rgba_img = img.convert('RGBA')
                            
                            # Create a solid white background image
                            background = Image.new('RGB', rgba_img.size, (255, 255, 255))
                            
                            # Paste the image using its alpha channel as a mask
                            background.paste(rgba_img, mask=rgba_img.split()[3])
                            converted_img = background
                        else:
                            converted_img = img.convert('RGB')
                            
                        converted_img.save(destination, format='JPEG', quality=95)
                    
                    elif fmt == 'PNG':
                        # Keep original modes (e.g., RGBA) or convert paletted/grayscale to preserve quality
                        if img.mode in ('P', '1'):
                            converted_img = img.convert('RGBA')
                        else:
                            converted_img = img
                            
                        converted_img.save(destination, format='PNG')
                        
            except Exception as e:
                print(f"Failed to process {file_path.name}: {e}")