import os
from PIL import Image, ImageFilter

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp", ".gif"}


def apply_blur(input_dir, output_dir, radius):
    """
    Apply a Gaussian blur of the given radius to every image in input_dir,
    saving the results into output_dir.

    Args:
        input_dir (str): Path to a directory containing images.
        output_dir (str): Path to a directory where blurred images are written.
                           Created if it doesn't already exist.
        radius (float): Gaussian blur radius. radius == 0 means the image is
                         copied through unchanged (passthrough). Negative
                         values are rejected.

    Raises:
        ValueError: If radius is negative.
        NotADirectoryError: If input_dir does not exist or isn't a directory.

    Returns:
        list[str]: Filenames that were processed and written to output_dir.
    """
    if radius < 0:
        raise ValueError(f"radius must be >= 0, got {radius}")

    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"input_dir does not exist: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    processed = []

    for filename in sorted(os.listdir(input_dir)):
        input_path = os.path.join(input_dir, filename)

        if not os.path.isfile(input_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext not in IMAGE_EXTENSIONS:
            continue

        output_path = os.path.join(output_dir, filename)

        with Image.open(input_path) as img:
            if radius == 0:
                # Passthrough: write out the image unchanged.
                blurred = img.copy()
            else:
                blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))

            # Preserve original format when possible (e.g. JPEG, PNG).
            save_kwargs = {}
            if img.format:
                save_kwargs["format"] = img.format

            blurred.save(output_path, **save_kwargs)

        processed.append(filename)

    return processed