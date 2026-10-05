"""Split images into R/G/B grayscale files and merge them back together.

Requires: Pillow  (pip install pillow)
"""

from pathlib import Path

from PIL import Image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def _has_alpha(img):
    """True if the image carries transparency information."""
    return img.mode in ("RGBA", "LA", "PA", "RGBa", "La") or "transparency" in img.info


def split_channels(input_dir, output_dir, include_alpha=False):
    """Split every image in input_dir into grayscale channel images.

    For an input named "photo.jpg", writes to output_dir:
        photo_R.png, photo_G.png, photo_B.png
    Each output is a single-channel ("L" mode) image where pixel brightness
    equals the intensity of that color channel. PNG is used so the channel
    data is saved losslessly.

    If include_alpha is True and the source image has an alpha channel (or
    palette/tRNS transparency), a fourth file photo_A.png is also written.
    Sources without alpha are unaffected by the flag; no _A file is created
    for them. When include_alpha is False (the default), alpha is discarded.

    Returns a list with one tuple of paths per input image:
    (r_path, g_path, b_path), or (r_path, g_path, b_path, a_path) when an
    alpha file was written for that image.
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
            if include_alpha and _has_alpha(img):
                # Normalize any mode (RGBA, LA, P w/ transparency, ...) to RGBA.
                channels = img.convert("RGBA").split()
                names = ("R", "G", "B", "A")
            else:
                # Normalize any mode to plain RGB; alpha is discarded.
                # Grayscale inputs yield identical channels.
                channels = img.convert("RGB").split()
                names = ("R", "G", "B")

        out_paths = tuple(output_dir / f"{path.stem}_{n}.png" for n in names)
        for channel, out_path in zip(channels, out_paths):
            # convert() can leave a stale RGB-tuple "transparency" entry in
            # .info, which PNG can't write for an L-mode image; drop it.
            channel.info.pop("transparency", None)
            channel.save(out_path)
        results.append(out_paths)

    return results


def merge_channels(r_path, g_path, b_path, output_path):
    """Combine three grayscale images into one RGB image.

    The files at r_path, g_path and b_path supply the red, green and blue
    channels respectively. All three must have identical dimensions.
    Use a lossless format (e.g. .png) for output_path to preserve exact values.

    Returns the output Path.
    """
    channels = []
    for p in (r_path, g_path, b_path):
        with Image.open(p) as img:
            channels.append(img.convert("L"))  # force single-channel

    if not (channels[0].size == channels[1].size == channels[2].size):
        sizes = [c.size for c in channels]
        raise ValueError(f"Channel images must be the same size, got {sizes}")

    merged = Image.merge("RGB", channels)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.save(output_path)
    return output_path


if __name__ == "__main__":
    # Example round trip:
    #   triples = split_channels("images", "channels")
    #   r, g, b = triples[0]
    #   merge_channels(r, g, b, "restored.png")
    pass