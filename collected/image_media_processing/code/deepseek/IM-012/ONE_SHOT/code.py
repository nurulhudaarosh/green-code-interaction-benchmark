import os
from pathlib import Path
from PIL import Image

def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """
    Resize all images in input_dir preserving aspect ratio, then pad to exactly
    target_size with content centered.

    Args:
        input_dir (str | Path): Directory containing source images.
        output_dir (str | Path): Directory to write processed images.
        target_size (tuple): (width, height) of the output images.
        pad_color (tuple): RGB(A) padding color, default black.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_w, target_h = target_size
    if target_w <= 0 or target_h <= 0:
        raise ValueError("target_size must be positive (width, height)")

    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

    for img_path in input_dir.iterdir():
        if not img_path.is_file() or img_path.suffix.lower() not in valid_exts:
            continue

        with Image.open(img_path) as im:
            im = im.convert("RGBA") if len(pad_color) == 4 else im.convert("RGB")
            src_w, src_h = im.size

            # Scale factor that fits the image inside target box
            scale = min(target_w / src_w, target_h / src_h)
            new_w = max(1, int(round(src_w * scale)))
            new_h = max(1, int(round(src_h * scale)))

            resized = im.resize((new_w, new_h), Image.LANCZOS)

            # Create padded canvas
            canvas = Image.new(resized.mode, (target_w, target_h), pad_color)

            # Center the resized image
            offset_x = (target_w - new_w) // 2
            offset_y = (target_h - new_h) // 2
            canvas.paste(resized, (offset_x, offset_y))

            # Save (preserve original extension)
            out_path = output_dir / img_path.name
            save_kwargs = {}
            if img_path.suffix.lower() in {".jpg", ".jpeg"}:
                canvas = canvas.convert("RGB")
                save_kwargs["quality"] = 95

            canvas.save(out_path, **save_kwargs)

    return output_dir