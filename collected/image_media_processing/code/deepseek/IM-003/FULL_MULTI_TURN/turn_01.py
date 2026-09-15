import os
from pathlib import Path
from PIL import Image

def convert_format(input_dir, output_dir, target_format):
    """
    Convert all images in input_dir to the target format (PNG or JPEG).
    
    Args:
        input_dir (str): Directory containing source images.
        output_dir (str): Directory where converted images will be saved.
        target_format (str): Either 'PNG' or 'JPEG' (case-insensitive).
    
    Returns:
        dict: Summary with 'converted', 'skipped', and 'failed' file lists.
    """
    target_format = target_format.upper()
    if target_format not in ("PNG", "JPEG"):
        raise ValueError("target_format must be 'PNG' or 'JPEG'")
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Map target format to PIL format name and extension
    pil_format = "JPEG" if target_format == "JPEG" else "PNG"
    extension = ".jpg" if target_format == "JPEG" else ".png"
    
    # Supported input extensions
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", 
                        ".tiff", ".tif", ".webp", ".ico"}
    
    result = {"converted": [], "skipped": [], "failed": []}
    
    for file_path in input_path.iterdir():
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in valid_extensions:
            result["skipped"].append(str(file_path))
            continue
        
        output_file = output_path / (file_path.stem + extension)
        
        # Avoid overwriting input if same dir + format
        if output_file.resolve() == file_path.resolve():
            result["skipped"].append(str(file_path))
            continue
        
        try:
            with Image.open(file_path) as img:
                img.load()  # Ensure image data is loaded before file handle closes
                
                if pil_format == "JPEG":
                    # Flatten transparency onto a white background
                    if img.mode in ("RGBA", "LA") or (
                        img.mode == "P" and "transparency" in img.info
                    ):
                        rgba = img.convert("RGBA")
                        background = Image.new("RGB", rgba.size, (255, 255, 255))
                        background.paste(rgba, mask=rgba.split()[-1])
                        img_to_save = background
                    elif img.mode == "P":
                        img_to_save = img.convert("RGB")
                    elif img.mode != "RGB":
                        img_to_save = img.convert("RGB")
                    else:
                        img_to_save = img
                    
                    img_to_save.save(output_file, "JPEG", quality=95, optimize=True)
                else:
                    # PNG: preserve alpha, convert palette-with-transparency to RGBA
                    if img.mode == "P" and "transparency" in img.info:
                        img_to_save = img.convert("RGBA")
                    elif img.mode not in ("RGB", "RGBA", "L", "LA", "I", "I;16", "1"):
                        img_to_save = img.convert("RGBA")
                    else:
                        img_to_save = img
                    
                    img_to_save.save(output_file, "PNG", optimize=True)
                
                result["converted"].append(str(output_file))
        
        except Exception as e:
            result["failed"].append((str(file_path), str(e)))
    
    return result


if __name__ == "__main__":
    summary = convert_format("input_images", "output_images", "JPEG")
    print(f"Converted: {len(summary['converted'])}")
    print(f"Skipped:   {len(summary['skipped'])}")
    print(f"Failed:    {len(summary['failed'])}")
    for path, err in summary["failed"]:
        print(f"  {path}: {err}")