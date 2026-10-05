from pathlib import Path
from PIL import Image


def split_channels(input_dir, output_dir):
    """
    Split every RGB image in input_dir into separate R, G, and B
    grayscale channel images.

    Output files:
        image_R.png
        image_G.png
        image_B.png

    Returns:
        A dictionary mapping each input filename to the generated paths.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

    for path in input_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in valid_extensions:
            continue

        try:
            with Image.open(path) as img:
                # Ensure the image has R/G/B channels.
                rgb = img.convert("RGB")
                r, g, b = rgb.split()

                stem = path.stem

                r_path = output_dir / f"{stem}_R.png"
                g_path = output_dir / f"{stem}_G.png"
                b_path = output_dir / f"{stem}_B.png"

                r.save(r_path)
                g.save(g_path)
                b.save(b_path)

                results[path.name] = {
                    "R": str(r_path),
                    "G": str(g_path),
                    "B": str(b_path),
                }

        except (OSError, ValueError):
            # Skip files that PIL cannot open as images.
            continue

    return results


def merge_channels(r_path, g_path, b_path, output_path):
    """
    Merge three grayscale R/G/B channel images into one RGB image.

    Returns:
        The output path.
    """
    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        r = r_img.convert("L")
        g = g_img.convert("L")
        b = b_img.convert("L")

        if r.size != g.size or r.size != b.size:
            raise ValueError("All three channel images must have the same dimensions.")

        merged = Image.merge("RGB", (r, g, b))

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged.save(output_path)

    return str(output_path)