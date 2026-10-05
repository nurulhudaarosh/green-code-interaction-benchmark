from pathlib import Path

from PIL import Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


def _validate_color(fill_color):
    try:
        r, g, b = fill_color
    except (TypeError, ValueError):
        raise ValueError("fill_color must be an (R, G, B) tuple") from None
    if not all(isinstance(v, int) and 0 <= v <= 255 for v in (r, g, b)):
        raise ValueError("fill_color values must be integers in 0-255")
    return r, g, b


def _fill_for_mode(mode, rgb):
    """Translate an RGB tuple into a fill value valid for the given image mode."""
    r, g, b = rgb
    if mode == "RGB":
        return (r, g, b)
    if mode == "RGBA":
        return (r, g, b, 255)
    gray = round(0.299 * r + 0.587 * g + 0.114 * b)
    if mode == "L":
        return gray
    if mode == "LA":
        return (gray, 255)
    raise ValueError(f"Unsupported mode: {mode}")


def rotate_and_crop(input_dir, output_dir, angle_degrees, crop_size, fill_color=(0, 0, 0)):
    """Rotate every image in input_dir and write it to output_dir at exactly crop_size.

    Args:
        input_dir:      directory containing images (non-recursive).
        output_dir:     directory to write results to (created if missing).
        angle_degrees:  counter-clockwise rotation angle in degrees.
        crop_size:      int (square) or (width, height) of the output images.
        fill_color:     (R, G, B) tuple, 0-255 each, used for padding and the
                        corners exposed by rotation. Default is black. For
                        grayscale images it is converted to its gray level;
                        for images with alpha the fill is fully opaque.

    Rotation uses expand=True, so nothing is clipped by the rotation itself.
    The rotated image is then centered on a crop_size canvas: if it is larger
    than the canvas in a dimension it is center-cropped, if smaller it is padded.

    Returns the list of output file paths.
    """
    if isinstance(crop_size, int):
        crop_w = crop_h = crop_size
    else:
        crop_w, crop_h = crop_size
    if crop_w <= 0 or crop_h <= 0:
        raise ValueError("crop_size must be positive")
    rgb = _validate_color(fill_color)

    input_dir, output_dir = Path(input_dir), Path(output_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(input_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue
        try:
            with Image.open(path) as im:
                im = ImageOps.exif_transpose(im)  # respect camera orientation
                if im.mode not in ("RGB", "RGBA", "L", "LA"):
                    has_alpha = im.mode in ("PA", "La", "RGBa") or "transparency" in im.info
                    im = im.convert("RGBA" if has_alpha else "RGB")

                fill = _fill_for_mode(im.mode, rgb)
                rotated = im.rotate(
                    angle_degrees, resample=Image.BICUBIC, expand=True, fillcolor=fill
                )

                # paste() clips negative offsets, which gives the center-crop for free.
                canvas = Image.new(rotated.mode, (crop_w, crop_h), fill)
                x = (crop_w - rotated.width) // 2
                y = (crop_h - rotated.height) // 2
                canvas.paste(rotated, (x, y))

                if path.suffix.lower() in {".jpg", ".jpeg"} and canvas.mode not in ("RGB", "L"):
                    canvas = canvas.convert("RGB")  # JPEG has no alpha

                out_path = output_dir / path.name
                canvas.save(out_path)
                written.append(out_path)
        except Exception as e:  # skip unreadable/corrupt files, keep going
            print(f"Skipping {path.name}: {e}")

    return written


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description=rotate_and_crop.__doc__.splitlines()[0])
    p.add_argument("input_dir")
    p.add_argument("output_dir")
    p.add_argument("angle", type=float)
    p.add_argument("width", type=int)
    p.add_argument("height", type=int, nargs="?")
    p.add_argument("--fill", type=int, nargs=3, metavar=("R", "G", "B"), default=(0, 0, 0))
    a = p.parse_args()
    size = (a.width, a.height or a.width)
    n = len(rotate_and_crop(a.input_dir, a.output_dir, a.angle, size, tuple(a.fill)))
    print(f"Wrote {n} images")