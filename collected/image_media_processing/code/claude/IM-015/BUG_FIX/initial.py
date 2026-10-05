from pathlib import Path
from PIL import Image

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def split_channels(input_dir, output_dir):
    """Split every image in input_dir into grayscale R, G, B files.

    For an input 'photo.jpg', writes photo_R.png, photo_G.png, photo_B.png
    to output_dir. PNG is used so the channel data is saved losslessly.
    Returns a list of (r_path, g_path, b_path) tuples, one per image.
    """
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue
        with Image.open(path) as img:
            r, g, b = img.convert("RGB").split()  # each is mode "L" (grayscale)

        out_paths = []
        for name, channel in (("R", r), ("G", g), ("B", b)):
            out = output_dir / f"{path.stem}_{name}.png"
            channel.save(out)
            out_paths.append(out)
        results.append(tuple(out_paths))
    return results


def merge_channels(r_path, g_path, b_path, output_path):
    """Combine three grayscale images (R, G, B) into one RGB image."""
    channels = []
    for p in (r_path, g_path, b_path):
        with Image.open(p) as img:
            channels.append(img.convert("L").copy())

    if len({c.size for c in channels}) != 1:
        raise ValueError(
            f"Channel sizes differ: {[c.size for c in channels]}"
        )

    merged = Image.merge("RGB", channels)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.save(output_path)
    return output_path


if __name__ == "__main__":
    # Example round trip
    split_channels("images", "channels")
    merge_channels(
        "channels/photo_R.png",
        "channels/photo_G.png",
        "channels/photo_B.png",
        "merged/photo.png",
    )