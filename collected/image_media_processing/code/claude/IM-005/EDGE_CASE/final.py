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
    # Modes that ImageFilter.GaussianBlur does not support directly.
    unsupported_blur_modes = {"P", "1"}
    processed = []

    for filename in sorted(os.listdir(input_dir)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue

        src_path = os.path.join(input_dir, filename)
        dst_path = os.path.join(output_dir, filename)

        with Image.open(src_path) as img:
            original_mode = img.mode

            # GaussianBlur can't operate on palette ("P") or 1-bit ("1") images
            # (e.g. small GIFs/PNGs, including 1x1 images, are often "P").
            # Convert to a blur-safe mode first, then convert back afterward.
            needs_mode_roundtrip = original_mode in unsupported_blur_modes
            work_img = img.convert("RGBA") if needs_mode_roundtrip else img

            if radius == 0:
                # Passthrough: no blur applied, just re-save.
                result = work_img.copy()
            else:
                # Works correctly for any image size, including 1x1 —
                # GaussianBlur is a convolution, not a rank filter, so it
                # has no minimum-dimension requirement.
                result = work_img.filter(ImageFilter.GaussianBlur(radius=radius))

            if needs_mode_roundtrip:
                result = result.convert(original_mode)

            # Handle formats that don't support alpha (e.g. JPEG) gracefully
            if ext in (".jpg", ".jpeg") and result.mode in ("RGBA", "P"):
                result = result.convert("RGB")

            result.save(dst_path)
            processed.append(filename)

    return processed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Apply Gaussian blur to all images in a directory.")
    parser.add_argument("input_dir", help="Directory containing source images")
    parser.add_argument("output_dir", help="Directory to write blurred images to")
    parser.add_argument("radius", type=float, help="Gaussian blur radius (0 = passthrough)")
    args = parser.parse_args()

    files = apply_blur(args.input_dir, args.output_dir, args.radius)
    print(f"Processed {len(files)} image(s): {files}")