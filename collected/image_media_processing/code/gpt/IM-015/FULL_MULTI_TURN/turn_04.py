id="74126"
from pathlib import Path
from PIL import Image


def split_channels(input_dir, output_dir, include_alpha=False):
    """
    Split images into R, G, B grayscale files.

    If include_alpha=True and the source has an alpha channel,
    also save <stem>_A.png.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_extensions = {
        ".jpg", ".jpeg", ".png", ".bmp",
        ".tif", ".tiff", ".webp"
    }

    for path in input_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in valid_extensions:
            continue

        with Image.open(path) as img:
            has_alpha = "A" in img.getbands()

            rgb = img.convert("RGB")
            r, g, b = rgb.split()

            r.save(output_dir / f"{path.stem}_R.png")
            g.save(output_dir / f"{path.stem}_G.png")
            b.save(output_dir / f"{path.stem}_B.png")

            if include_alpha and has_alpha:
                alpha = img.getchannel("A")
                alpha.save(output_dir / f"{path.stem}_A.png")


def merge_channels(r_path, g_path, b_path, output_path):
    """
    Merge three grayscale channel images into an RGB image.

    The three images must have identical dimensions, including
    valid dimensions such as 1x1.
    """
    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        # Explicitly check dimensions before Image.merge().
        if r_img.size != g_img.size or r_img.size != b_img.size:
            raise ValueError(
                "Channel images must have matching dimensions: "
                f"R={r_img.size}, G={g_img.size}, B={b_img.size}"
            )

        # Convert to grayscale. This also handles different source modes.
        r = r_img.convert("L")
        g = g_img.convert("L")
        b = b_img.convert("L")

        # Image.merge() supports 1x1 images normally.
        rgb = Image.merge("RGB", (r, g, b))

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rgb.save(output_path)