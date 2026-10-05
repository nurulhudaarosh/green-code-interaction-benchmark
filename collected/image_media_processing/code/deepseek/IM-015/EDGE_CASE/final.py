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

        r.save(os.path.join(output_dir, f"{name}_R.png"))
        g.save(os.path.join(output_dir, f"{name}_G.png"))
        b.save(os.path.join(output_dir, f"{name}_B.png"))

        print(f"Split {filename} -> {name}_R.png, {name}_G.png, {name}_B.png")


def merge_channels(r_path, g_path, b_path, output_path):
    """
    Combine three single-channel (grayscale) images into one RGB image.

    The three inputs must have identical dimensions. Works for any size,
    including 1x1 images.
    """
    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        # Convert to 'L' (8-bit grayscale) so merge works with single bands
        r = r_img.convert("L")
        g = g_img.convert("L")
        b = b_img.convert("L")

        # Size check works for any dimensions, including 1x1
        if not (r.size == g.size == b.size):
            raise ValueError(
                f"Size mismatch: R={r.size}, G={g.size}, B={b.size}"
            )

        merged = Image.merge("RGB", (r, g, b))

    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)

    # Make sure we're saving as RGB (defensive, in case merge behavior changes)
    merged = merged.convert("RGB")
    merged.save(output_path)
    print(f"Merged channels -> {output_path} (size={merged.size}, mode={merged.mode})")
    return merged


# ---- Round-trip test, including the 1x1 edge case -------------------------
def test_1x1_roundtrip(tmpdir="test_channels"):
    os.makedirs(tmpdir, exist_ok=True)

    # Build a known 1x1 RGB image: pixel = (10, 20, 30)
    src = Image.new("RGB", (1, 1), (10, 20, 30))
    src_path = os.path.join(tmpdir, "one.png")
    src.save(src_path)

    # Split it
    split_dir = os.path.join(tmpdir, "split")
    split_channels(tmpdir, split_dir)

    # Merge it back
    out_path = os.path.join(tmpdir, "one_reconstructed.png")
    merged = merge_channels(
        os.path.join(split_dir, "one_R.png"),
        os.path.join(split_dir, "one_G.png"),
        os.path.join(split_dir, "one_B.png"),
        out_path,
    )

    # Verify
    assert merged.size == (1, 1), f"Expected 1x1, got {merged.size}"
    assert merged.mode == "RGB", f"Expected RGB, got {merged.mode}"

    with Image.open(out_path) as reopened:
        assert reopened.size == (1, 1)
        assert reopened.mode == "RGB"
        assert reopened.getpixel((0, 0)) == (10, 20, 30), \
            f"Pixel mismatch: {reopened.getpixel((0, 0))}"

    print("1x1 round-trip OK: pixel =", reopened.getpixel((0, 0)))


if __name__ == "__main__":
    test_1x1_roundtrip()