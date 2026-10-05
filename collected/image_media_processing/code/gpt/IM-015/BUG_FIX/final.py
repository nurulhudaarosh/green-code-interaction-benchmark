from PIL import Image
import os


def split_channels(input_dir, output_dir):
    """
    Split every image in input_dir into R, G, and B grayscale images.
    """
    os.makedirs(output_dir, exist_ok=True)

    results = {}
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)

        if not os.path.isfile(input_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue

        try:
            with Image.open(input_path) as img:
                img = img.convert("RGB")

                r, g, b = img.split()
                base_name = os.path.splitext(filename)[0]

                r_path = os.path.join(output_dir, f"{base_name}_R.png")
                g_path = os.path.join(output_dir, f"{base_name}_G.png")
                b_path = os.path.join(output_dir, f"{base_name}_B.png")

                r.save(r_path)
                g.save(g_path)
                b.save(b_path)

                results[filename] = {
                    "R": r_path,
                    "G": g_path,
                    "B": b_path
                }

        except Exception as e:
            print(f"Skipping {filename}: {e}")

    return results


def merge_channels(r_path, g_path, b_path, output_path):
    """
    Merge three grayscale channel images into one RGB image.

    Raises:
        ValueError: If the three channel images do not have identical dimensions.
    """

    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        # Explicitly validate dimensions before attempting the merge.
        if r_img.size != g_img.size or r_img.size != b_img.size:
            raise ValueError(
                f"Channel image dimensions must match: "
                f"R={r_img.size}, G={g_img.size}, B={b_img.size}."
            )

        # Convert channels to grayscale after validation.
        r = r_img.convert("L")
        g = g_img.convert("L")
        b = b_img.convert("L")

        merged = Image.merge("RGB", (r, g, b))

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        merged.save(output_path)

        return output_path