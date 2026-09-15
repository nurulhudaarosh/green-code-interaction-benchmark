"""
convert_format.py

Convert all images in a directory to PNG or JPEG, safely flattening
transparency onto a solid background when converting to JPEG (since
JPEG has no alpha channel).

Requires: Pillow (`pip install Pillow`)
"""

import os
from pathlib import Path
from PIL import Image, UnidentifiedImageError

# Extensions we'll attempt to read as images.
SUPPORTED_INPUT_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif",
    ".webp", ".ico", ".ppm", ".pgm",
}


def convert_format(
    input_dir: str,
    output_dir: str,
    target_format: str,
    background_color: tuple = (255, 255, 255),
    quality: int = 95,
    overwrite: bool = True,
) -> list:
    """
    Convert all images found in `input_dir` to `target_format` ("PNG" or "JPEG"),
    writing results into `output_dir`.

    Transparency handling:
        - If the target format is JPEG (which doesn't support alpha),
          any image with transparency (mode RGBA, LA, P with transparency,
          etc.) is flattened onto `background_color` before saving.
        - If the target format is PNG, transparency is preserved as-is.

    Args:
        input_dir: Directory containing source images (scanned non-recursively).
        output_dir: Directory where converted images will be written (created if needed).
        target_format: "PNG" or "JPEG" (case-insensitive; "JPG" accepted as alias).
        background_color: RGB tuple used to flatten transparency for JPEG output.
        quality: JPEG quality (1-95 recommended range; ignored for PNG).
        overwrite: If False, skip files that already exist in output_dir.

    Returns:
        List of (input_path, output_path_or_None, status) tuples describing
        the outcome for each file, where status is "converted", "skipped",
        or "error: <message>".
    """
    target_format = target_format.strip().upper()
    if target_format == "JPG":
        target_format = "JPEG"
    if target_format not in ("PNG", "JPEG"):
        raise ValueError(f"target_format must be 'PNG' or 'JPEG', got {target_format!r}")

    in_path = Path(input_dir)
    out_path = Path(output_dir)

    if not in_path.is_dir():
        raise NotADirectoryError(f"input_dir does not exist or is not a directory: {input_dir}")

    out_path.mkdir(parents=True, exist_ok=True)

    ext = ".jpg" if target_format == "JPEG" else ".png"
    results = []

    for entry in sorted(in_path.iterdir()):
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
            continue

        dest_file = out_path / (entry.stem + ext)

        if dest_file.exists() and not overwrite:
            results.append((str(entry), str(dest_file), "skipped"))
            continue

        try:
            with Image.open(entry) as img:
                # Force load now, so errors surface here rather than at save time.
                img.load()
                converted = _prepare_image_for_format(img, target_format, background_color)

                save_kwargs = {}
                if target_format == "JPEG":
                    save_kwargs["quality"] = quality
                    save_kwargs["optimize"] = True
                else:  # PNG
                    save_kwargs["optimize"] = True

                converted.save(dest_file, format=target_format, **save_kwargs)

            results.append((str(entry), str(dest_file), "converted"))

        except UnidentifiedImageError:
            results.append((str(entry), None, "error: not a recognized image file"))
        except Exception as e:  # noqa: BLE001 - we want to report and continue
            results.append((str(entry), None, f"error: {e}"))

    return results


def _prepare_image_for_format(img: Image.Image, target_format: str, background_color: tuple) -> Image.Image:
    """
    Return a copy of `img` ready to be saved as `target_format`.

    - For JPEG: flattens any transparency onto `background_color` and
      ensures the final mode is RGB (JPEG doesn't support alpha or palettes
      with transparency).
    - For PNG: preserves transparency, just normalizes palette images with
      a transparency entry into RGBA so it's stored explicitly.
    """
    has_alpha = _has_transparency(img)

    if target_format == "JPEG":
        if has_alpha:
            # Normalize to RGBA first so compositing is well-defined,
            # regardless of original mode (P, LA, etc.).
            rgba = img.convert("RGBA")
            background = Image.new("RGB", rgba.size, background_color)
            # Use the alpha channel as the mask when pasting.
            background.paste(rgba, mask=rgba.split()[3])
            return background
        else:
            # No transparency, just ensure RGB (handles CMYK, L, P without alpha, etc.)
            if img.mode != "RGB":
                return img.convert("RGB")
            return img.copy()

    else:  # PNG
        if has_alpha:
            return img.convert("RGBA")
        # Preserve simple modes as-is if already fine; convert P without
        # transparency issues to RGB for consistent output, but keep L/RGB.
        if img.mode in ("RGB", "RGBA", "L", "LA"):
            return img.copy()
        return img.convert("RGB")


def _has_transparency(img: Image.Image) -> bool:
    """Detect whether an image carries any transparency information."""
    if img.mode in ("RGBA", "LA"):
        return True
    if img.mode == "P" and "transparency" in img.info:
        return True
    # Some images expose an 'A' band via getbands() even outside common modes.
    if "A" in img.getbands():
        return True
    return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert all images in a directory to PNG or JPEG.")
    parser.add_argument("input_dir", help="Directory containing source images")
    parser.add_argument("output_dir", help="Directory to write converted images")
    parser.add_argument("target_format", help="'PNG' or 'JPEG'")
    parser.add_argument("--bg", nargs=3, type=int, default=(255, 255, 255),
                         metavar=("R", "G", "B"),
                         help="Background color used to flatten transparency for JPEG (default: white)")
    parser.add_argument("--quality", type=int, default=95, help="JPEG quality (default: 95)")
    parser.add_argument("--no-overwrite", action="store_true", help="Skip files that already exist in output_dir")

    args = parser.parse_args()

    results = convert_format(
        args.input_dir,
        args.output_dir,
        args.target_format,
        background_color=tuple(args.bg),
        quality=args.quality,
        overwrite=not args.no_overwrite,
    )

    converted = sum(1 for _, _, status in results if status == "converted")
    skipped = sum(1 for _, _, status in results if status == "skipped")
    errors = [(src, status) for src, _, status in results if status.startswith("error")]

    print(f"Converted: {converted}, Skipped: {skipped}, Errors: {len(errors)}")
    for src, status in errors:
        print(f"  {src}: {status}")