import os
from pathlib import Path
from PIL import Image


def _has_alpha(img):
    """Return True if the image has any transparency that needs flattening."""
    if img.mode in ("RGBA", "LA"):
        return True
    if img.mode == "P" and "transparency" in img.info:
        return True
    return False


def _flatten_on_white(img):
    """Composite an image with transparency onto a solid white background,
    returning an RGB image. Non-transparent images are converted to RGB
    directly (no compositing needed)."""
    if _has_alpha(img):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])  # alpha as mask
        return background
    # No alpha -> plain RGB conversion is safe (no transparency to lose)
    return img.convert("RGB")


def convert_format(input_dir, output_dir, target_format):
    """
    Convert all images in input_dir to the target format (PNG or JPEG).

    For JPEG output, any transparency in the source is flattened onto a
    WHITE background (transparent pixels become white, not black).
    """
    target_format = target_format.upper()
    if target_format not in ("PNG", "JPEG"):
        raise ValueError("target_format must be 'PNG' or 'JPEG'")

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")

    output_path.mkdir(parents=True, exist_ok=True)

    pil_format = "JPEG" if target_format == "JPEG" else "PNG"
    extension = ".jpg" if target_format == "JPEG" else ".png"

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif",
                        ".tiff", ".tif", ".webp", ".ico"}

    result = {"converted": [], "skipped": [], "failed": []}

    for file_path in input_path.iterdir():
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in valid_extensions:
            result["skipped"].append(str(file_path))
            continue

        output_file = output_path / (file_path.stem + extension)
        if output_file.resolve() == file_path.resolve():
            result["skipped"].append(str(file_path))
            continue

        try:
            with Image.open(file_path) as img:
                img.load()

                if pil_format == "JPEG":
                    # Flatten onto white to avoid black transparent regions.
                    img_to_save = _flatten_on_white(img)
                    img_to_save.save(output_file, "JPEG", quality=95, optimize=True)
                else:
                    # PNG: preserve alpha where possible.
                    if img.mode == "P" and "transparency" in img.info:
                        img_to_save = img.convert("RGBA")
                    elif img.mode not in ("RGB", "RGBA", "L", "LA",
                                          "I", "I;16", "1"):
                        img_to_save = img.convert("RGBA")
                    else:
                        img_to_save = img
                    img_to_save.save(output_file, "PNG", optimize=True)

                result["converted"].append(str(output_file))

        except Exception as e:
            result["failed"].append((str(file_path), str(e)))

    return result


if __name__ == "__main__":
    summary = convert_format("input_images", "output_images", "JPEG")
    print(f"Converted: {len(summary['converted'])}")
    print(f"Skipped:   {len(summary['skipped'])}")
    print(f"Failed:    {len(summary['failed'])}")
    for path, err in summary["failed"]:
        print(f"  {path}: {err}")