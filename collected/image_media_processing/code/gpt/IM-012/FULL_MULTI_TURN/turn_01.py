from pathlib import Path
from PIL import Image


def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """
    Resize images while preserving aspect ratio, then pad them to exactly
    target_size with the content centered.

    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory where processed images are saved.
        target_size (tuple): Target size as (width, height).
        pad_color (tuple): RGB color used for padding.

    Returns:
        None
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_w, target_h = target_size

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

    for image_path in input_dir.iterdir():
        if not image_path.is_file() or image_path.suffix.lower() not in valid_extensions:
            continue

        with Image.open(image_path) as img:
            # Ensure RGB output
            img = img.convert("RGB")

            src_w, src_h = img.size

            # Preserve aspect ratio while ensuring the image fits
            scale = min(target_w / src_w, target_h / src_h)

            new_w = round(src_w * scale)
            new_h = round(src_h * scale)

            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Create target canvas
            canvas = Image.new("RGB", (target_w, target_h), pad_color)

            # Center the resized image
            x = (target_w - new_w) // 2
            y = (target_h - new_h) // 2

            canvas.paste(resized, (x, y))

            # Save with original filename
            output_path = output_dir / image_path.name
            canvas.save(output_path)