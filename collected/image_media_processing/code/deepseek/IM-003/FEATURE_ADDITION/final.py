import os
from pathlib import Path
from PIL import Image, ImageOps

# Supported input formats
INPUT_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'}

# Target format configuration
FORMAT_CONFIG = {
    'png':  {'ext': '.png', 'pil_format': 'PNG'},
    'jpeg': {'ext': '.jpg', 'pil_format': 'JPEG'},
}

DEFAULT_BACKGROUND = (255, 255, 255)


def _validate_background_color(color):
    """Ensure background_color is a 3-tuple of ints in [0, 255]."""
    if (not isinstance(color, (tuple, list))
            or len(color) != 3
            or not all(isinstance(c, int) and 0 <= c <= 255 for c in color)):
        raise ValueError(
            f"background_color must be an RGB tuple of ints in 0..255, got {color!r}"
        )
    return tuple(color)


def _flatten_transparency(img, background=DEFAULT_BACKGROUND):
    """Composite an image with alpha onto an opaque background."""
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        rgba = img.convert('RGBA')
        bg = Image.new('RGB', rgba.size, background)
        bg.paste(rgba, mask=rgba.split()[-1])  # alpha channel as mask
        return bg
    if img.mode not in ('RGB', 'L'):
        return img.convert('RGB')
    return img


def convert_format(input_dir, output_dir, target_format, background_color=DEFAULT_BACKGROUND):
    """
    Convert all images in input_dir to target_format ('png' or 'jpeg')
    and write them to output_dir.

    Args:
        input_dir: Directory containing source images.
        output_dir: Directory to write converted images into (created if needed).
        target_format: 'png' or 'jpeg' (case-insensitive).
        background_color: RGB tuple used to flatten alpha when target is JPEG.
                          Ignored for PNG output. Defaults to white (255, 255, 255).

    Returns:
        dict with 'converted', 'skipped', and 'failed' entries.
    """
    target_format = target_format.lower().strip()
    if target_format not in FORMAT_CONFIG:
        raise ValueError(f"target_format must be 'png' or 'jpeg', got {target_format!r}")

    background_color = _validate_background_color(background_color)

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {input_dir}")

    output_path.mkdir(parents=True, exist_ok=True)

    config = FORMAT_CONFIG[target_format]
    out_ext = config['ext']
    pil_format = config['pil_format']

    results = {'converted': [], 'skipped': [], 'failed': []}

    for src in sorted(input_path.iterdir()):
        if not src.is_file():
            continue

        ext = src.suffix.lower()
        if ext not in INPUT_EXTENSIONS:
            results['skipped'].append(str(src))
            continue

        # Skip files already in the target format
        if target_format == 'jpeg' and ext in ('.jpg', '.jpeg'):
            results['skipped'].append(str(src))
            continue
        if target_format == 'png' and ext == '.png':
            results['skipped'].append(str(src))
            continue

        dest = output_path / (src.stem + out_ext)

        try:
            with Image.open(src) as img:
                # Preserve EXIF orientation if present
                try:
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    pass

                if target_format == 'jpeg':
                    img = _flatten_transparency(img, background=background_color)
                    img.save(dest, pil_format, quality=95, optimize=True)
                else:  # png
                    if img.mode not in ('RGB', 'RGBA', 'L', 'LA', 'P'):
                        img = img.convert('RGBA')
                    img.save(dest, pil_format, optimize=True)

            results['converted'].append(str(dest))
        except Exception as e:
            results['failed'].append((str(src), str(e)))

    return results