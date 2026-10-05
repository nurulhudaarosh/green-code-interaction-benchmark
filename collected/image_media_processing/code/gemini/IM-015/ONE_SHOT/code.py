import os
from pathlib import Path
from PIL import Image

# Supported image extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}

def split_channels(input_dir: str, output_dir: str) -> None:
    """
    Splits all images in input_dir into red, green, and blue grayscale channel images
    and saves them in output_dir.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for file_path in input_path.iterdir():
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        try:
            with Image.open(file_path) as img:
                # Convert image to RGB mode if it isn't already (e.g., RGBA, Grayscale)
                rgb_img = img.convert('RGB')
                r, g, b = rgb_img.split()

                stem = file_path.stem
                r.save(output_path / f"{stem}_R.png")
                g.save(output_path / f"{stem}_G.png")
                b.save(output_path / f"{stem}_B.png")

                print(f"Successfully split: {file_path.name}")
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

def merge_channels(r_path: str, g_path: str, b_path: str, output_path: str) -> None:
    """
    Recombines three single-channel grayscale images (R, G, B) back into a single RGB image.
    """
    try:
        with Image.open(r_path) as r_img, Image.open(g_path) as g_img, Image.open(b_path) as b_img:
            # Ensure images are in single-channel grayscale mode ('L')
            r = r_img.convert('L')
            g = g_img.convert('L')
            b = b_img.convert('L')

            # Ensure all three channel images match in dimensions
            if not (r.size == g.size == b.size):
                raise ValueError(f"Dimensions do not match: R={r.size}, G={g.size}, B={b.size}")

            # Merge channels and save
            merged_img = Image.merge('RGB', (r, g, b))
            
            # Create destination directory if it does not exist
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            merged_img.save(output_path)
            
            print(f"Successfully merged channels into: {output_path}")
    except Exception as e:
        print(f"Error merging channels: {e}")