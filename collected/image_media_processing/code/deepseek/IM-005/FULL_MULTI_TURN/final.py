import os
import shutil
from PIL import Image, ImageFilter


def apply_blur(input_dir, output_dir, radius, filter_type='gaussian'):
    """
    Apply a blur of the given radius to every image in input_dir,
    saving the results to output_dir.

    Args:
        input_dir (str): Directory containing source images.
        output_dir (str): Directory to write blurred images to.
        radius (float): Blur radius. 0 means passthrough (byte-identical copy).
                        Negative values are rejected.
        filter_type (str): 'gaussian' (default) or 'box'.

    Raises:
        ValueError: If radius is negative, or filter_type is not recognized.
        NotADirectoryError: If input_dir is not a directory.
    """
    if radius < 0:
        raise ValueError(f"radius must be non-negative, got {radius}")
    if filter_type not in ('gaussian', 'box'):
        raise ValueError(
            f"filter_type must be 'gaussian' or 'box', got {filter_type!r}"
        )
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"input_dir is not a directory: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    filter_cls = ImageFilter.GaussianBlur if filter_type == 'gaussian' else ImageFilter.BoxBlur

    for filename in os.listdir(input_dir):
        src_path = os.path.join(input_dir, filename)
        if not os.path.isfile(src_path):
            continue

        dst_path = os.path.join(output_dir, filename)

        if radius == 0:
            # True passthrough: copy raw bytes, no decode/encode round-trip.
            shutil.copyfile(src_path, dst_path)
            continue

        try:
            with Image.open(src_path) as img:
                img.load()

                # 1x1 (and any small) images: Pillow's separable blur handles
                # edge clamping, but we still verify the output shape to be safe.
                out = img.filter(filter_cls(radius=radius))
                out.load()

                if out.size != img.size:
                    raise RuntimeError(
                        f"{filter_type} blur changed image size for {filename}: "
                        f"{img.size} -> {out.size}"
                    )

                out.save(dst_path)
        except (IOError, OSError):
            # Skip files that aren't valid images.
            continue