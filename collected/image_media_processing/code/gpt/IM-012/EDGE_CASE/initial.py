from pathlib import Path
from PIL import Image


def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """
    Resize images while preserving aspect ratio, then pad them to exactly
    target_size with the content centered.

    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory where resized images are saved.
        target_size (tuple): Target size as (width, height).
        pad_color (tuple): RGB color used for padding.

    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_w, target_h = target_size

    for file_path in input_dir.iterdir():
        if not file_path.is_file():
            continue

        try:
            with Image.open(file_path) as img:
                img = img.convert("RGB")

                src_w, src_h = img.size

                # Scale so the entire image fits inside target_size
                scale = min(target_w / src_w, target_h / src_h)

                new_w = max(1, round(src_w * scale))
                new_h = max(1, round(src_h * scale))

                # Resize while preserving aspect ratio
                resized = img.resize(
                    (new_w, new_h),
                    Image.Resampling.LANCZOS
                )

                # Create target canvas
                canvas = Image.new(
                    "RGB",
                    (target_w, target_h),
                    pad_color
                )

                # Center the resized image
                x = (target_w - new_w) // 2
                y = (target_h - new_h) // 2

                canvas.paste(resized, (x, y))

                # Save using the original filename
                canvas.save(output_dir / file_path.name)

        except (OSError, ValueError):
            # Skip files that are not valid images
            continue