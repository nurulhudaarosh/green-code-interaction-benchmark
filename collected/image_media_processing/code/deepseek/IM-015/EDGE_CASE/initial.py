import os
from PIL import Image


def split_channels(input_dir, output_dir):
    """
    Split every image in input_dir into separate R, G, B grayscale images
    saved in output_dir.

    For an image named 'foo.png', outputs:
        foo_R.png, foo_G.png, foo_B.png
    """
    os.makedirs(output_dir, exist_ok=True)

    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

    for filename in os.listdir(input_dir):
        name, ext = os.path.splitext(filename)
        if ext.lower() not in valid_exts:
            continue

        in_path = os.path.join(input_dir, filename)
        try:
            with Image.open(in_path) as img:
                rgb = img.convert("RGB")
                r, g, b = rgb.split()
        except (OSError, ValueError) as e:
            print(f"Skipping {filename}: {e}")
            continue

        # Save each channel as an 8-bit grayscale image
        r.save(os.path.join(output_dir, f"{name}_R.png"))
        g.save(os.path.join(output_dir, f"{name}_G.png"))
        b.save(os.path.join(output_dir, f"{name}_B.png"))

        print(f"Split {filename} -> {name}_R.png, {name}_G.png, {name}_B.png")


def merge_channels(r_path, g_path, b_path, output_path):
    """
    Combine three single-channel (grayscale) images into one RGB image.

    The three inputs must have identical dimensions.
    """
    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        # Convert to 'L' (8-bit grayscale) so .split()/.merge() work cleanly
        r = r_img.convert("L")
        g = g_img.convert("L")
        b = b_img.convert("L")

        if not (r.size == g.size == b.size):
            raise ValueError(
                f"Size mismatch: R={r.size}, G={g.size}, B={b.size}"
            )

        merged = Image.merge("RGB", (r, g, b))

    # Ensure output directory exists
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)

    merged.save(output_path)
    print(f"Merged channels -> {output_path}")
    return merged


# ---- Example usage ---------------------------------------------------------
if __name__ == "__main__":
    split_channels("images/", "channels/")

    merge_channels(
        "channels/foo_R.png",
        "channels/foo_G.png",
        "channels/foo_B.png",
        "reconstructed/foo.png",
    )