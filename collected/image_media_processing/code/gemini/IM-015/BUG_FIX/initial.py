import os
from PIL import Image

def split_channels(input_dir: str, output_dir: str) -> None:
    """
    Splits all images in input_dir into single-channel grayscale R, G, and B images,
    saving them to output_dir with suffixes _R.png, _G.png, and _B.png.
    """
    os.makedirs(output_dir, exist_ok=True)
    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        file_path = os.path.join(input_dir, filename)
        base_name, _ = os.path.splitext(filename)

        with Image.open(file_path) as img:
            # Convert image to RGB mode if it isn't already (e.g., RGBA, Grayscale)
            rgb_img = img.convert('RGB')
            r, g, b = rgb_img.split()

            # Save individual channels as grayscale images
            r.save(os.path.join(output_dir, f"{base_name}_R.png"))
            g.save(os.path.join(output_dir, f"{base_name}_G.png"))
            b.save(os.path.join(output_dir, f"{base_name}_B.png"))


def merge_channels(r_path: str, g_path: str, b_path: str, output_path: str) -> None:
    """
    Recombines three single-channel grayscale images (R, G, B) into a single RGB image.
    """
    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        # Ensure all channels are loaded as single-channel grayscale ('L' mode)
        r = r_img.convert('L')
        g = g_img.convert('L')
        b = b_img.convert('L')

        # Verify matching dimensions before merging
        if not (r.size == g.size == b.size):
            raise ValueError(f"Image dimensions do not match: R={r.size}, G={g.size}, B={b.size}")

        # Merge channels into an RGB image
        merged_img = Image.merge('RGB', (r, g, b))
        
        # Create output directory if it doesn't exist
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        merged_img.save(output_path)