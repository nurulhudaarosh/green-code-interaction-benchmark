import os
import shutil
from PIL import Image, ImageFilter

def apply_blur(input_dir, output_dir, radius):
    """
    Apply a Gaussian blur to every image in input_dir and save the
    results (with the same filenames) into output_dir.

    radius == 0  -> byte-identical passthrough (raw file copy, no re-encode)
    radius > 0   -> Gaussian blur applied via Pillow
    radius < 0   -> ValueError
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

        if radius == 0:
            # Byte-identical passthrough: copy the file directly.
            # Do NOT open/save via Pillow here — re-encoding (even with no
            # filter applied) can change compressed bytes, strip metadata,
            # or alter palette/precision in ways that fail a byte-identity
            # check.
            shutil.copyfile(src_path, dst_path)
        else:
            with Image.open(src_path) as img:
                blurred = img.filter(ImageFilter.GaussianBlur(radius))
                blurred.save(dst_path)

        processed.append(filename)

    return processed