import os
from pathlib import Path
from PIL import Image

# Formats we consider "images" for conversion
INPUT_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff",
    ".webp", ".ico", ".ppm", ".pgm", ".pbm", ".jp2", ".pcx",
}

SUPPORTED_TARGETS = {"PNG", "JPEG", "JPG"}


def convert_format(input_dir, output_dir, target_format):
    """
    Convert all images in input_dir to the given target format and write
    them to output_dir.

    Args:
        input_dir (str | Path): Directory containing source images.
        output_dir (str | Path): Directory to write converted images into.
        target_format (str): "PNG", "JPEG", or "JPG" (case-insensitive).

    Returns:
        dict: {"converted": [...paths...], "skipped": [...], "failed": [(path, err), ...]}
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    target_format = target_format.upper()

    if target_format not in SUPPORTED_TARGETS:
        raise ValueError(
            f"Unsupported target format: {target_format!r}. "
            f"Expected one of {sorted(SUPPORTED_TARGETS)}."
        )
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Normalize the extension / PIL format name
    is_jpeg = target_format in ("JPEG", "JPG")
    pil_format = "JPEG" if is_jpeg else "PNG"
    out_ext = ".jpg" if is_jpeg else ".png"

    converted, skipped, failed = [], [], []

    for src in sorted(input_dir.rglob("*")):
        if not src.is_file():
            continue
        if src.suffix.lower() not in INPUT_EXTENSIONS:
            skipped.append(src)
            continue

        # Preserve subdirectory structure relative to input_dir
        rel = src.relative_to(input_dir)
        dst = (output_dir / rel).with_suffix(out_ext)
        dst.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(src) as img:
                if is_jpeg:
                    img = _flatten_for_jpeg(img)
                    img.save(dst, format="JPEG", quality=95, optimize=True)
                else:
                    # PNG supports alpha; ensure RGBA if there is any transparency
                    if img.mode in ("RGBA", "LA") or (
                        img.mode == "P" and "transparency" in img.info
                    ):
                        img = img.convert("RGBA")
                    img.save(dst, format="PNG", optimize=True)
            converted.append(dst)
        except Exception as e:
            failed.append((src, e))

    return {"converted": converted, "skipped": skipped, "failed": failed}


def _flatten_for_jpeg(img):
    """
    Return an RGB copy of `img` suitable for JPEG encoding, compositing any
    transparency over a white background.
    """
    # Palette images with transparency -> RGBA first
    if img.mode == "P" and "transparency" in img.info:
        img = img.convert("RGBA")

    if img.mode in ("RGBA", "LA"):
        # Composite over white
        background = Image.new("RGB", img.size, (255, 255, 255))
        # Use the alpha channel as a mask
        alpha = img.getchannel("A") if img.mode == "RGBA" else img.split()[-1]
        background.paste(img.convert("RGB"), mask=alpha)
        return background

    if img.mode != "RGB":
        # CMYK, L, 1, I;16, etc. -> straightforward RGB conversion
        return img.convert("RGB")

    return img


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python convert_format.py <input_dir> <output_dir> <PNG|JPEG>")
        sys.exit(1)
    result = convert_format(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"Converted: {len(result['converted'])}")
    print(f"Skipped:   {len(result['skipped'])}")
    print(f"Failed:    {len(result['failed'])}")
    for path, err in result["failed"]:
        print(f"  ! {path}: {err}")