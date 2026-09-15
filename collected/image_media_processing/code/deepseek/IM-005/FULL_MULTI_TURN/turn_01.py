import os
from PIL import Image, ImageFilter


def apply_blur(input_dir, output_dir, radius):
    """
    Apply a Gaussian blur of the given radius to every image in input_dir,
    saving the results to output_dir.

    Args:
        input_dir (str): Directory containing source images.
        output_dir (str): Directory to write blurred images to.
        radius (float): Gaussian blur radius. 0 means passthrough (copy).
                        Negative values are rejected.

    Raises:
        ValueError: If radius is negative.
        NotADirectoryError: If input_dir is not a directory.
    """
    if radius < 0:
        raise ValueError(f"radius must be non-negative, got {radius}")
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"input_dir is not a directory: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        src_path = os.path.join(input_dir, filename)
        if not os.path.isfile(src_path):
            continue

        dst_path = os.path.join(output_dir, filename)

        try:
            with Image.open(src_path) as img:
                img.load()
                if radius == 0:
                    out = img.copy()
                else:
                    out = img.filter(ImageFilter.GaussianBlur(radius=radius))
                out.save(dst_path)
        except (IOError, OSError):
            # Skip files that aren't valid images.
            continue