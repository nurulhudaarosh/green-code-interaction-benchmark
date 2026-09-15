import os
from PIL import Image, ImageFilter


def apply_blur(input_dir, output_dir, radius):
    """
    Apply a Gaussian blur of the given radius to every image in input_dir,
    saving the results (with the same filenames) into output_dir.

    Parameters
    ----------
    input_dir : str
        Path to the directory containing source images.
    output_dir : str
        Path to the directory where blurred images will be written.
        Created if it doesn't exist.
    radius : float
        Gaussian blur radius. radius == 0 means "passthrough" (image is
        copied/re-saved unchanged). Negative values raise ValueError.

    Returns
    -------
    list[str]
        Filenames that were processed.

    Raises
    ------
    ValueError
        If radius is negative.
    NotADirectoryError
        If input_dir does not exist or is not a directory.
    """
    if radius < 0:
        raise ValueError(f"radius must be >= 0, got {radius}")

    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"input_dir does not exist: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    valid_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}
    processed = []

    for filename in sorted(os.listdir(input_dir)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue

        src_path = os.path.join(input_dir, filename)
        dst_path = os.path.join(output_dir, filename)

        with Image.open(src_path) as img:
            if radius == 0:
                # Passthrough: no blur applied, just re-save (preserves format/mode)
                result = img.copy()
            else:
                result = img.filter(ImageFilter.GaussianBlur(radius=radius))

            # Handle formats that don't support alpha (e.g. JPEG) gracefully
            save_kwargs = {}
            if ext in (".jpg", ".jpeg") and result.mode in ("RGBA", "P"):
                result = result.convert("RGB")

            result.save(dst_path, **save_kwargs)
            processed.append(filename)

    return processed


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Apply Gaussian blur to all images in a directory.")
    parser.add_argument("input_dir", help="Directory containing source images")
    parser.add_argument("output_dir", help="Directory to write blurred images to")
    parser.add_argument("radius", type=float, help="Gaussian blur radius (0 = passthrough)")
    args = parser.parse_args()

    files = apply_blur(args.input_dir, args.output_dir, args.radius)
    print(f"Processed {len(files)} image(s): {files}")