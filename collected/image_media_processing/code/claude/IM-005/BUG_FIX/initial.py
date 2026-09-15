import os
from PIL import Image, ImageFilter

def apply_blur(input_dir, output_dir, radius):
    """
    Apply a Gaussian blur to every image in input_dir and save the
    results (with the same filenames) into output_dir.

    Parameters
    ----------
    input_dir : str
        Directory containing the source images.
    output_dir : str
        Directory where blurred images will be written (created if missing).
    radius : float
        Gaussian blur radius. radius == 0 means "no blur" (image is copied
        as-is). Negative values raise ValueError.

    Returns
    -------
    list[str]
        Filenames that were processed.
    """
    if radius < 0:
        raise ValueError(f"radius must be >= 0, got {radius}")

    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"input_dir does not exist: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}
    processed = []

    for filename in sorted(os.listdir(input_dir)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_exts:
            continue

        src_path = os.path.join(input_dir, filename)
        dst_path = os.path.join(output_dir, filename)

        with Image.open(src_path) as img:
            if radius == 0:
                # Passthrough: just save a copy, preserving mode/format.
                result = img.copy()
            else:
                result = img.filter(ImageFilter.GaussianBlur(radius))

            # Preserve original format when possible (Pillow infers it from
            # the extension on save, but GIFs/format-specific info like
            # palette can get lost — copy() above keeps mode intact).
            result.save(dst_path)

        processed.append(filename)

    return processed