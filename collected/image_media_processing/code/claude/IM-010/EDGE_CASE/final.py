from pathlib import Path

from PIL import Image, ImageColor, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


def _resolve_fill(fill_color, mode):
    """Convert a user-supplied color into a value valid for the given image mode.

    None -> black for L/RGB, fully transparent for RGBA.
    Accepts color names/hex strings, an int, or an RGB/RGBA tuple.
    """
    if fill_color is None:
        return (0, 0, 0, 0) if mode == "RGBA" else (0 if mode == "L" else (0, 0, 0))
    if isinstance(fill_color, str):
        return ImageColor.getcolor(fill_color, mode)
    if isinstance(fill_color, int):
        fill_color = (fill_color,) * 3
    rgb = tuple(fill_color[:3])
    if mode == "L":
        return Image.new("RGB", (1, 1), rgb).convert("L").getpixel((0, 0))
    if mode == "RGBA":
        alpha = fill_color[3] if len(fill_color) == 4 else 255
        return rgb + (alpha,)
    return rgb


def rotate_and_crop(input_dir, output_dir, angle_degrees, crop_size, fill_color=None):
    """Rotate every image in input_dir and save it to output_dir at exactly crop_size.

    Args:
        input_dir:     folder containing the source images.
        output_dir:    folder to write results to (created if missing).
        angle_degrees: counter-clockwise rotation angle.
        crop_size:     int (square) or (width, height) of the output images.
        fill_color:    color for rotated corners AND padding (name, hex string,
                       int, or RGB/RGBA tuple). Default: black, or transparent
                       for images with an alpha channel.

    The image is rotated with expand=True so rotation clips nothing, then placed
    centered on a canvas of exactly crop_size. Each axis is handled independently:
    larger than crop_size -> center-cropped; smaller -> padded with fill_color on
    both sides (including when crop_size exceeds the rotated image in both axes).

    Returns:
        List of output file paths.
    """
    target_w, target_h = (crop_size, crop_size) if isinstance(crop_size, int) else crop_size
    if target_w <= 0 or target_h <= 0:
        raise ValueError(f"crop_size must be positive, got {crop_size!r}")

    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for path in sorted(input_dir.iterdir()):
        if path.suffix.lower() not in IMAGE_EXTS:
            continue
        try:
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img)  # respect camera orientation
                if img.mode not in ("RGB", "RGBA", "L"):
                    img = img.convert("RGBA" if "A" in img.getbands() else "RGB")

                fill = _resolve_fill(fill_color, img.mode)

                # Use the same fill for the corners exposed by rotation so they
                # match the padding added below.
                rotated = img.rotate(
                    angle_degrees, resample=Image.BICUBIC, expand=True, fillcolor=fill
                )

                # Negative offsets crop, positive offsets pad; both are centered.
                canvas = Image.new(rotated.mode, (target_w, target_h), fill)
                offset = ((target_w - rotated.width) // 2, (target_h - rotated.height) // 2)
                canvas.paste(rotated, offset)

                # JPEG has no alpha channel
                if path.suffix.lower() in {".jpg", ".jpeg"} and canvas.mode == "RGBA":
                    canvas = canvas.convert("RGB")

                out_path = output_dir / path.name
                canvas.save(out_path)
                written.append(out_path)
        except Exception as exc:  # skip unreadable/corrupt files, keep going
            print(f"Skipping {path.name}: {exc}")
    return written


if __name__ == "__main__":
    import sys

    if len(sys.argv) not in (5, 6):
        sys.exit("usage: rotate_and_crop.py INPUT_DIR OUTPUT_DIR ANGLE CROP_SIZE [FILL_COLOR]")
    rotate_and_crop(
        sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]),
        sys.argv[5] if len(sys.argv) == 6 else None,
    )