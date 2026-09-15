from pathlib import Path
from PIL import Image

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp"}


def convert_format(input_dir, output_dir, target_format):
    """
    Convert all images in input_dir to target_format ('PNG' or 'JPEG'),
    saving results into output_dir. Transparency is safely flattened
    onto a white background when converting to JPEG (which has no
    alpha channel support).

    Args:
        input_dir: Path to directory containing source images.
        output_dir: Path to directory where converted images are saved.
        target_format: 'PNG' or 'JPEG' (case-insensitive).

    Returns:
        List of output file paths that were successfully created.
    """
    target_format = target_format.strip().upper()
    if target_format in ("JPG",):
        target_format = "JPEG"
    if target_format not in ("PNG", "JPEG"):
        raise ValueError("target_format must be 'PNG' or 'JPEG'")

    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    if not in_dir.is_dir():
        raise NotADirectoryError(f"input_dir does not exist: {in_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    ext = ".jpg" if target_format == "JPEG" else ".png"
    written = []

    for path in sorted(in_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTS:
            continue

        try:
            with Image.open(path) as img:
                img.load()  # force load before any lazy-mode issues on close

                if target_format == "JPEG":
                    img = _flatten_to_rgb(img)
                    save_kwargs = {"quality": 95, "optimize": True}
                else:  # PNG
                    if img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
                        img = img.convert("RGBA")
                    save_kwargs = {"optimize": True}

                out_path = out_dir / (path.stem + ext)
                img.save(out_path, format=target_format, **save_kwargs)
                written.append(out_path)

        except Exception as e:
            print(f"Skipping '{path.name}': {e}")

    return written


def _flatten_to_rgb(img, background=(255, 255, 255)):
    """
    Flatten any transparency (alpha channel or palette transparency)
    onto a solid background and return an RGB image safe for JPEG.
    """
    # Normalize palette images that might carry transparency info
    if img.mode == "P":
        if "transparency" in img.info:
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

    if img.mode in ("RGBA", "LA"):
        # Build an RGBA base, composite over solid background, drop alpha
        rgba = img.convert("RGBA")
        flat = Image.new("RGBA", rgba.size, background + (255,))
        flat.alpha_composite(rgba)
        return flat.convert("RGB")

    if img.mode != "RGB":
        img = img.convert("RGB")

    return img