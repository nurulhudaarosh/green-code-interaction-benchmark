import os
from PIL import Image


def split_channels(input_dir: str, output_dir: str) -> None:
    """Splits all images in input_dir into red, green, and blue grayscale channels

    and saves them in output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    supported_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")

    for file_name in os.listdir(input_dir):
        if not file_name.lower().endswith(supported_extensions):
            continue

        file_path = os.path.join(input_dir, file_name)
        base_name, ext = os.path.splitext(file_name)

        with Image.open(file_path) as img:
            # Convert to RGB mode in case image is RGBA, Greyscale, or Palette
            rgb_img = img.convert("RGB")
            r, g, b = rgb_img.split()

            r.save(os.path.join(output_dir, f"{base_name}_R{ext}"))
            g.save(os.path.join(output_dir, f"{base_name}_G{ext}"))
            b.save(os.path.join(output_dir, f"{base_name}_B{ext}"))


def merge_channels(
    r_path: str, g_path: str, b_path: str, output_path: str
) -> None:
    """Recombines three grayscale image channels (R, G, B) into a single color image.

    Correctly handles 1x1 pixel images and validates matching dimensions.
    """
    with Image.open(r_path) as r_img, Image.open(g_path) as g_img, Image.open(
        b_path
    ) as b_img:

        r = r_img.convert("L")
        g = g_img.convert("L")
        b = b_img.convert("L")

        # Ensure all single channels match in dimensions (e.g. 1x1 == 1x1 == 1x1)
        if not (r.size == g.size == b.size):
            raise ValueError(
                f"Image dimensions do not match: R={r.size}, G={g.size}, B={b.size}"
            )

        merged = Image.merge("RGB", (r, g, b))

        # Safe directory creation: handles relative paths like 'output.png' where dirname is ''
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        merged.save(output_path)