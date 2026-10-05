import os
from PIL import Image

def merge_channels(r_path: str, g_path: str, b_path: str, output_path: str) -> None:
    """
    Loads three grayscale images representing R, G, and B channels and merges
    them into a single RGB image after verifying they have matching dimensions.
    """
    with Image.open(r_path) as r_img, Image.open(g_path) as g_img, Image.open(b_path) as b_img:
        if not (r_img.size == g_img.size == b_img.size):
            raise ValueError(
                f"Image dimensions do not match: "
                f"R={r_img.size}, G={g_img.size}, B={b_img.size}"
            )
            
        r_channel = r_img.convert('L')
        g_channel = g_img.convert('L')
        b_channel = b_img.convert('L')
        
        merged_img = Image.merge('RGB', (r_channel, g_channel, b_channel))
        
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        merged_img.save(output_path)