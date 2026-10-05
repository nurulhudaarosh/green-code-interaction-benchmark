from pathlib import Path
from PIL import Image


def split_channels(input_dir, output_dir):
    """
    Split every RGB image in input_dir into R, G, and B grayscale images.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_extensions = {
        ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"
    }

    for image_path in input_dir.iterdir():
        if image_path.suffix.lower() not in valid_extensions:
            continue

        with Image.open(image_path) as img:
            r, g, b = img.convert("RGB").split()

            stem = image_path.stem
            r.save(output_dir / f"{stem}_R.png")
            g.save(output_dir / f"{stem}_G.png")
            b.save(output_dir / f"{stem}_B.png")


def merge_channels(r_path, g_path, b_path, output_path):
    """
    Merge three grayscale channel images into an RGB image.

    Supports images of any valid size, including 1x1 pixels.
    """
    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        r = r_img.convert("L")
        g = g_img.convert("L")
        b = b_img.convert("L")

        # Matching dimensions are required, including for 1x1 images.
        if r.size != g.size or r.size != b.size:
            raise ValueError(
                f"Channel dimensions must match: "
                f"R={r.size}, G={g.size}, B={b.size}"
            )

        # Image.merge supports 1x1 images normally.
        merged = Image.merge("RGB", (r, g, b))
        merged.save(output_path)


# Example: 1x1 RGB image
if __name__ == "__main__":
    Image.new("L", (1, 1), 255).save("r.png")
    Image.new("L", (1, 1), 128).save("g.png")
    Image.new("L", (1, 1), 64).save("b.png")

    merge_channels("r.png", "g.png", "b.png", "output.png")

    with Image.open("output.png") as img:
        assert img.size == (1, 1)
        assert img.mode == "RGB"

    print("Successfully created 1x1 RGB image.")