from pathlib import Path
from PIL import Image
import sys


def split_channels(input_dir, output_dir):
    """
    Split every image in `input_dir` into separate R, G, B grayscale images,
    saving them into `output_dir` as <stem>_R.png, <stem>_G.png, <stem>_B.png.

    Returns a list of tuples: (source_path, (r_path, g_path, b_path))
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
    results = []

    for src in sorted(input_dir.iterdir()):
        if not src.is_file() or src.suffix.lower() not in extensions:
            continue

        with Image.open(src) as img:
            rgb = img.convert("RGB")
            r, g, b = rgb.split()          # each is mode "L" (grayscale)

            base = output_dir / src.stem
            r_path = base.with_name(base.name + "_R.png")
            g_path = base.with_name(base.name + "_G.png")
            b_path = base.with_name(base.name + "_B.png")

            r.save(r_path)
            g.save(g_path)
            b.save(b_path)

        results.append((src, (r_path, g_path, b_path)))
        print(f"split: {src.name} -> {r_path.name}, {g_path.name}, {b_path.name}")

    return results


def merge_channels(r_path, g_path, b_path, output_path):
    """
    Recombine three single-channel (grayscale) images into an RGB image.
    All three must have identical dimensions.
    """
    r_path, g_path, b_path = Path(r_path), Path(g_path), Path(b_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        r = r_img.convert("L")
        g = g_img.convert("L")
        b = b_img.convert("L")

        if not (r.size == g.size == b.size):
            raise ValueError(
                f"Size mismatch: R={r.size}, G={g.size}, B={b.size}"
            )

        merged = Image.merge("RGB", (r, g, b))
        merged.save(output_path)

    print(f"merged: {r_path.name}, {g_path.name}, {b_path.name} -> {output_path.name}")
    return output_path


# ---------------- Demo / CLI ----------------
if __name__ == "__main__":
    if len(sys.argv) == 3:
        # python script.py <input_dir> <output_dir>
        split_channels(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python channels.py <input_dir> <output_dir>")