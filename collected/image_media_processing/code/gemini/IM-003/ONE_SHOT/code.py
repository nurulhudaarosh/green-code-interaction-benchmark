import os
from PIL import Image

def convert_format(input_dir, output_dir, target_format):
    """
    Converts all images in input_dir to the specified target_format.
    
    :param input_dir: Path to source directory.
    :param output_dir: Path to destination directory.
    :param target_format: 'JPEG' (or 'JPG') or 'PNG'.
    """
    # Normalize target format name
    target_format = target_format.strip().upper()
    if target_format == "JPG":
        target_format = "JPEG"
    
    if target_format not in ("JPEG", "PNG"):
        raise ValueError("Target format must be 'JPEG' or 'PNG'.")
    
    # Ensure destination directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Target extension for saved files
    out_ext = ".jpg" if target_format == "JPEG" else ".png"
    
    # Supported input extensions
    valid_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"}
    
    for filename in os.listdir(input_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue
            
        src_path = os.path.join(input_dir, filename)
        base_name = os.path.splitext(filename)[0]
        dest_path = os.path.join(output_dir, base_name + out_ext)
        
        try:
            with Image.open(src_path) as img:
                # Handle JPEG conversion and transparency flattening
                if target_format == "JPEG":
                    # Check if the image has an alpha channel or transparency
                    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                        # Convert palette image with transparency to RGBA first
                        rgba_img = img.convert("RGBA")
                        
                        # Create a solid white background image
                        background = Image.new("RGB", rgba_img.size, (255, 255, 255))
                        
                        # Composite the image onto the white background using the alpha channel as a mask
                        background.paste(rgba_img, mask=rgba_img.split()[3])
                        final_img = background
                    else:
                        final_img = img.convert("RGB")
                    
                    final_img.save(dest_path, "JPEG", quality=95)
                
                # Handle PNG conversion
                elif target_format == "PNG":
                    # Retain original mode (RGB or RGBA), convert paletted/grayscale formats
                    if img.mode not in ("RGB", "RGBA"):
                        final_img = img.convert("RGBA") if "transparency" in img.info or img.mode == "P" else img.convert("RGB")
                    else:
                        final_img = img
                        
                    final_img.save(dest_path, "PNG")

                print(f"Converted: {filename} -> {os.path.basename(dest_path)}")
                
        except Exception as e:
            print(f"Failed to process {filename}: {e}")

# Example Usage:
# convert_format("./input_folder", "./output_folder", "JPEG")