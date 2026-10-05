"""Split images into R/G/B grayscale files and merge them back together.

Requires Pillow:  pip install pillow
"""
from pathlib import Path

from PIL import Image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".gif"}


def split_channels(input_dir, output_dir):
    """Split every image in `input_dir` into three grayscale PNGs.

    For an input named `photo.jpg`, writes `photo_R.png`, `photo_G.png`
    and `photo_B.png` into `output_dir` (created if missing). Each output
    is an 8-bit grayscale image holding that channel's intensities.
    PNG is used so the channel data is saved losslessly.

    Returns a list of (r_path, g_path, b_path) tuples, one per image.
    """
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        with Image.open(path) as img:
            # Normalise any mode (RGBA, P, L, CMYK...) to plain RGB.
            # Transparency is discarded.
            channels = img.convert("RGB").split()

        out_paths = []
        for name, channel in zip("RGB", channels):
            out = output_dir / f"{path.stem}_{name}.png"
            channel.save(out)  # each band is already mode "L" (grayscale)
            out_paths.append(out)
        results.append(tuple(out_paths))

    return results


def merge_channels(r_path, g_path, b_path, output_path):
    """Combine three grayscale images into one RGB image.

    The files are used as the red, green and blue channels respectively.
    All three must have the same dimensions. The format of `output_path`
    is chosen from its extension (use .png to stay lossless).

    Returns the output path as a Path.
    """
    channels = []
    for p in (r_path, g_path, b_path):
        with Image.open(p) as img:
            channels.append(img.convert("L"))  # force single-channel grayscale

    # Validate before merging so the caller gets a clear error, not a
    # cryptic one from inside Pillow.
    if not (channels[0].size == channels[1].size == channels[2].size):
        raise ValueError(
            "Channel images must have identical dimensions (width, height), got: "
            f"R={channels[0].size} ({r_path}), "
            f"G={channels[1].size} ({g_path}), "
            f"B={channels[2].size} ({b_path})"
        )

    merged = Image.merge("RGB", channels)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.save(output_path)
    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 4 and sys.argv[1] == "split":
        split_channels(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 6 and sys.argv[1] == "merge":
        merge_channels(*sys.argv[2:6])
    else:
        print("Usage:\n  python channels.py split <input_dir> <output_dir>\n"
              "  python channels.py merge <r> <g> <b> <output>")