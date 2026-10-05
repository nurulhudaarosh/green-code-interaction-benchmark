import os
from pathlib import Path
from PIL import Image


def split_channels(input_dir, output_dir):
    """
    Split every image in input_dir into separate R, G, B grayscale images
    saved into output_dir.

    Output filenames follow the pattern:
        <stem>_R.png, <stem>_G.png, <stem>_B.png

    Args:
        input_dir (str | Path): folder containing source images
        output_dir (str | Path): folder to write channel images into
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in valid_exts:
            continue

        with Image.open(path) as img:
            rgb = img.convert("RGB")
            r, g, b = rgb.split()

            stem = path.stem
            r.save(output_dir / f"{stem}_R.png")
            g.save(output_dir / f"{stem}_G.png")
            b.save(output_dir / f"{stem}_B.png")

        print(f"Split {path.name} -> {stem}_R/G/B.png")


def merge_channels(r_path, g_path, b_path, output_path):
    """
    Recombine three single-channel grayscale images into one RGB image.

    Args:
        r_path (str | Path): red channel image
        g_path (str | Path): green channel image
        b_path (str | Path): blue channel image
        output_path (str | Path): where to save the merged RGB image
    """
    r_path = Path(r_path)
    g_path = Path(g_path)
    b_path = Path(b_path)
    output_path = Path(output_path)

    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        r = r_img.convert("L")
        g = g_img.convert("L")
        b = b_img.convert("L")

        if not (r.size == g.size == b.size):
            raise ValueError(
                f"Channel sizes differ: R={r.size}, G={g.size}, B={b.size}"
            )

        merged = Image.merge("RGB", (r, g, b))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.save(output_path)
    print(f"Merged channels -> {output_path}")


# ----------------------------------------------------------------------
# Example usage
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Split all images in ./images into ./channels
    split_channels("images", "channels")

    # Recombine one set back into a full RGB image
    merge_channels(
        "channels/photo_R.png",
        "channels/photo_G.png",
        "channels/photo_B.png",
        "reconstructed/photo.png",
    )