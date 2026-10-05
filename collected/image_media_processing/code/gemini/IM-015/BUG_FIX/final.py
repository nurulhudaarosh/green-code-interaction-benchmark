import os
from PIL import Image

def merge_channels(r_path: str, g_path: str, b_path: str, output_path: str) -> None:
    """
    Recombines three single-channel grayscale images (R, G, B) into a single RGB image.
    Explicitly verifies matching dimensions before processing.
    """
    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        # 1. Early validation of dimensions prior to processing
        if not (r_img.size == g_img.size == b_img.size):
            raise ValueError(
                f"Cannot merge channels due to dimension mismatch: "
                f"R={r_img.size}, G={g_img.size}, B={b_img.size}"
            )

        # 2. Convert to grayscale single-channel mode ('L')
        r = r_img.convert('L')
        g = g_img.convert('L')
        b = b_img.convert('L')

        # 3. Merge channels and save
        merged_img = Image.merge('RGB', (r, g, b))
        
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        merged_img.save(output_path)