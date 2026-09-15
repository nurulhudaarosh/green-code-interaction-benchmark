import os
from pathlib import Path
from PIL import Image

# Supported input extensions
INPUT_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif', '.webp', '.ico'}

# Map target format to PIL format name and output extension
FORMAT_MAP = {
    'png': ('PNG', '.png'),
    'jpeg': ('JPEG', '.jpg'),
    'jpg': ('JPEG', '.jpg'),
}


def convert_format(input_dir, output_dir, target_format, bg_color=(255, 255, 255), quality=95):
    """
    Convert all images in input_dir to the target format and save to output_dir.

    Every supported image is re-encoded through the pipeline, including images
    that already match the target format. This normalizes compression, strips
    metadata, and ensures transparency is flattened consistently for JPEG.

    Args:
        input_dir (str | Path): Directory containing source images.
        output_dir (str | Path): Directory to write converted images.
        target_format (str): Either 'PNG' or 'JPEG' (case-insensitive).
        bg_color (tuple): RGB background used to flatten transparency for JPEG.
        quality (int): JPEG quality (1-100).

    Returns:
        dict: Summary with 'converted' and 'failed' lists.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {input_dir}")

    fmt_key = target_format.lower().lstrip('.')
    if fmt_key not in FORMAT_MAP:
        raise ValueError(f"Unsupported target format: {target_format!r}. Use 'PNG' or 'JPEG'.")
    pil_format, out_ext = FORMAT_MAP[fmt_key]
    is_jpeg = pil_format == 'JPEG'

    # Guard against writing output back into the input directory, which would
    # cause files to be reprocessed (and potentially overwritten) on the same run.
    try:
        same_dir = input_dir.resolve() == output_dir.resolve()
    except FileNotFoundError:
        same_dir = False
    if same_dir:
        raise ValueError("input_dir and output_dir must be different directories.")

    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {'converted': [], 'failed': []}

    for src in sorted(input_dir.iterdir()):
        if not src.is_file() or src.suffix.lower() not in INPUT_EXTENSIONS:
            continue

        dst = output_dir / (src.stem + out_ext)

        # Avoid overwriting by appending a counter if the file already exists.
        # This also handles the case where the source was already the target
        # format and would otherwise collide with a same-named output file.
        counter = 1
        while dst.exists():
            dst = output_dir / f"{src.stem}_{counter}{out_ext}"
            counter += 1

        try:
            with Image.open(src) as img:
                img.load()  # ensure pixel data is available before closing

                if is_jpeg:
                    img = _flatten_for_jpeg(img, bg_color)
                    img.save(dst, pil_format, quality=quality, optimize=True, progressive=True)
                else:
                    # Preserve transparency for PNG
                    if img.mode not in ('RGB', 'RGBA', 'L', 'LA', 'P', 'I', '1', 'I;16'):
                        img = img.convert('RGBA')
                    img.save(dst, pil_format, optimize=True)

            summary['converted'].append(str(dst))
        except Exception as e:
            summary['failed'].append((str(src), str(e)))

    return summary


def _flatten_for_jpeg(img, bg_color):
    """Flatten an image onto an opaque RGB background suitable for JPEG."""
    # Handle palette images with transparency
    if img.mode == 'P':
        img = img.convert('RGBA')

    # Already opaque
    if img.mode in ('RGB', 'L'):
        return img.convert('RGB')

    # Composite alpha over the background
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        background = Image.new('RGB', img.size, bg_color)
        # Use the alpha channel as the mask
        background.paste(img, mask=img.split()[-1])
        return background

    # Fallback for other modes (e.g., CMYK, I;16)
    return img.convert('RGB')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Convert images to PNG or JPEG.")
    parser.add_argument('input_dir')
    parser.add_argument('output_dir')
    parser.add_argument('target_format', choices=['png', 'PNG', 'jpeg', 'JPEG', 'jpg', 'JPG'])
    parser.add_argument('--quality', type=int, default=95, help='JPEG quality (default 95)')
    parser.add_argument('--bg', default='255,255,255',
                        help='JPEG background color as R,G,B (default 255,255,255)')
    args = parser.parse_args()

    bg = tuple(int(x) for x in args.bg.split(','))
    result = convert_format(args.input_dir, args.output_dir, args.target_format,
                            bg_color=bg, quality=args.quality)

    print(f"Converted: {len(result['converted'])}")
    print(f"Failed:    {len(result['failed'])}")
    for path, err in result['failed']:
        print(f"  FAILED {path}: {err}")