from pathlib import Path
from PIL import Image


def split_channels(input_dir, output_dir):
    """
    Split every image in input_dir into separate R, G, B grayscale files.
    
    For each image 'foo.png' in input_dir, creates:
        output_dir/foo_R.png
        output_dir/foo_G.png
        output_dir/foo_B.png
    
    Non-RGB images (e.g. grayscale) are converted to RGB first.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Common image extensions; adjust as needed
    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

    processed = 0
    for img_path in sorted(input_dir.iterdir()):
        if not img_path.is_file() or img_path.suffix.lower() not in valid_exts:
            continue

        with Image.open(img_path) as img:
            rgb = img.convert("RGB")
            r, g, b = rgb.split()  # each is mode 'L' (grayscale)

            stem = img_path.stem
            r.save(output_dir / f"{stem}_R.png")
            g.save(output_dir / f"{stem}_G.png")
            b.save(output_dir / f"{stem}_B.png")

        processed += 1

    print(f"Split {processed} image(s) into R/G/B channels in {output_dir}")


def merge_channels(r_path, g_path, b_path, output_path):
    """
    Combine three grayscale images (R, G, B) into a single RGB image.
    
    Each input should be a single-channel (grayscale) image. If not,
    it will be converted to grayscale ('L') before merging.
    """
    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        r = r_img.convert("L")
        g = g_img.convert("L")
        b = b_img.convert("L")

        # Verify all channels share the same dimensions
        if not (r.size == g.size == b.size):
            raise ValueError(
                f"Channel sizes differ: R={r.size}, G={g.size}, B={b.size}"
            )

        merged = Image.merge("RGB", (r, g, b))

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged.save(output_path)

    print(f"Merged channels into {output_path}")


# --- Example usage ---
if __name__ == "__main__":
    # 1) Split all images in ./images into ./channels
    split_channels("images", "channels")

    # 2) Recombine a specific set of channels
    merge_channels(
        "channels/photo_R.png",
        "channels/photo_G.png",
        "channels/photo_B.png",
        "reconstructed/photo.png",
    )