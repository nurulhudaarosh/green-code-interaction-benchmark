import os
from PIL import Image

def split_channels(input_dir: str, output_dir: str, include_alpha: bool = False) -> None:
    """
    Splits all images in input_dir into separate red, green, and blue grayscale
    channel images and saves them to output_dir.
    
    If include_alpha is True and the image contains an alpha channel, 
    a fourth '<stem>_A.png' grayscale image is also saved.
    """
    os.makedirs(output_dir, exist_ok=True)
    supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(supported_extensions):
            image_path = os.path.join(input_dir, filename)
            
            with Image.open(image_path) as img:
                base_name, _ = os.path.splitext(filename)
                
                # Check for alpha channel support when requested
                has_alpha = include_alpha and img.mode in ('RGBA', 'LA', 'PA') or 'A' in img.getbands()
                
                if has_alpha:
                    rgba_img = img.convert('RGBA')
                    r, g, b, a = rgba_img.split()
                    a.save(os.path.join(output_dir, f"{base_name}_A.png"))
                else:
                    rgb_img = img.convert('RGB')
                    r, g, b = rgb_img.split()

                r.save(os.path.join(output_dir, f"{base_name}_R.png"))
                g.save(os.path.join(output_dir, f"{base_name}_G.png"))
                b.save(os.path.join(output_dir, f"{base_name}_B.png"))


def merge_channels(r_path: str, g_path: str, b_path: str, output_path: str, a_path: str = None) -> None:
    """
    Loads grayscale images representing R, G, B (and optionally A) channels 
    and merges them into a single RGB or RGBA image after verifying matching dimensions.
    """
    channels_to_open = {'R': r_path, 'G': g_path, 'B': b_path}
    if a_path:
        channels_to_open['A'] = a_path

    images = {key: Image.open(path) for key, path in channels_to_open.items()}

    try:
        sizes = {key: img.size for key, img in images.items()}
        first_size = next(iter(sizes.values()))
        
        if not all(size == first_size for size in sizes.values()):
            dim_str = ", ".join(f"{k}={v}" for k, v in sizes.items())
            raise ValueError(f"Image dimensions do not match: {dim_str}")

        converted_channels = [img.convert('L') for img in images.values()]
        
        mode = 'RGBA' if a_path else 'RGB'
        merged_img = Image.merge(mode, converted_channels)

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        merged_img.save(output_path)
    finally:
        for img in images.values():
            img.close()