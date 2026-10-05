from pathlib import Path
from PIL import Image


def letterbox_resize(
    input_dir,
    output_dir,
    target_size,
    pad_color=(0, 0, 0),
    align="center"
):
    """
    Resize images while preserving aspect ratio and pad them to exactly
    target_size.

    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory for processed images.
        target_size (tuple): Target size as (width, height).
        pad_color (tuple): RGB padding color.
        align (str): Placement of resized content:
                     "center"   -> centered in the canvas
                     "top-left" -> placed at the top-left corner.

    Raises:
        ValueError: If align is not "center" or "top-left".
    """
    if align not in {"center", "top-left"}:
        raise ValueError("align must be either 'center' or 'top-left'")

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_w, target_h = target_size

    valid_extensions = {
        ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"
    }

    for image_path in input_dir.iterdir():
        if (
            not image_path.is_file()
            or image_path.suffix.lower() not in valid_extensions
        ):
            continue

        with Image.open(image_path) as img:
            img = img.convert("RGB")

            src_w, src_h = img.size

            # Ensure the resized image fits within target_size.
            scale = min(
                target_w / src_w,
                target_h / src_h
            )

            new_w = round(src_w * scale)
            new_h = round(src_h * scale)

            resized = img.resize(
                (new_w, new_h),
                Image.Resampling.LANCZOS
            )

            # Create the final padded canvas.
            canvas = Image.new(
                "RGB",
                (target_w, target_h),
                pad_color
            )

            # Determine placement.
            if align == "center":
                x = (target_w - new_w) // 2
                y = (target_h - new_h) // 2
            else:  # top-left
                x = 0
                y = 0

            canvas.paste(resized, (x, y))

            output_path = output_dir / image_path.name
            canvas.save(output_path)