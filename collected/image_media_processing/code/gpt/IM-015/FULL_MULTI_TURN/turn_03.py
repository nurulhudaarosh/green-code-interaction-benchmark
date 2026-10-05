id="58321"
from pathlib import Path
from PIL import Image


def split_channels(input_dir, output_dir, include_alpha=False):
    """
    Split images into R, G, B grayscale files.

    If include_alpha=True and the source image has an alpha channel,
    also save <stem>_A.png.

    Returns:
        None
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
            # Detect whether the source has an alpha channel.
            has_alpha = "A" in img.getbands()

            # Always create RGB channels.
            rgb = img.convert("RGB")
            r, g, b = rgb.split()

            r.save(output_dir / f"{path.stem}_R.png")
            g.save(output_dir / f"{path.stem}_G.png")
            b.save(output_dir / f"{path.stem}_B.png")

            # Save alpha channel only when requested and available.
            if include_alpha and has_alpha:
                alpha = img.getchannel("A")
                alpha.save(output_dir / f"{path.stem}_A.png")


def merge_channels(r_path, g_path, b_path, output_path):
    """
    Merge three grayscale channel images into a single RGB image.

    Raises:
        ValueError: If the three channel images have different dimensions.
    """
    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        # Validate dimensions before Image.merge().
        if r_img.size != g_img.size or r_img.size != b_img.size:
            raise ValueError(
                "Channel images must have matching dimensions: "
                f"R={r_img.size}, G={g_img.size}, B={b_img.size}"
            )

        r = r_img.convert("L")
        g = g_img.convert("L")
        b = b_img.convert("L")

        rgb = Image.merge("RGB", (r, g, b))

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rgb.save(output_path)