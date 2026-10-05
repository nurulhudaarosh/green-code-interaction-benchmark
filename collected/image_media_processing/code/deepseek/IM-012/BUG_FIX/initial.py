import os
from pathlib import Path
from PIL import Image

def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """
    Resize all images in input_dir to fit within target_size while preserving
    aspect ratio, then pad to exactly target_size with the content centered.

    Args:
        input_dir (str | Path): Directory containing source images.
        output_dir (str | Path): Directory to write resized images to.
        target_size (tuple[int, int]): Desired output size as (width, height).
        pad_color (tuple[int, int, int]): RGB padding color. Default black.

    Returns:
        list[Path]: Paths of the saved output images.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_w, target_h = target_size
    if target_w <= 0 or target_h <= 0:
        raise ValueError("target_size dimensions must be positive")

    saved = []
    for path in sorted(input_dir.iterdir()):
        if not path.is_file():
            continue
        try:
            with Image.open(path) as im:
                im = im.convert("RGB")
                src_w, src_h = im.size

                # Scale factor that fits the image inside the target box
                scale = min(target_w / src_w, target_h / src_h)
                new_w = max(1, int(round(src_w * scale)))
                new_h = max(1, int(round(src_h * scale)))

                resized = im.resize((new_w, new_h), Image.LANCZOS)

                # Create canvas filled with pad color and paste centered
                canvas = Image.new("RGB", (target_w, target_h), pad_color)
                offset_x = (target_w - new_w) // 2
                offset_y = (target_h - new_h) // 2
                canvas.paste(resized, (offset_x, offset_y))

                out_path = output_dir / path.name
                canvas.save(out_path)
                saved.append(out_path)
        except (UnidentifiedImageError := Exception):
            # Skip files that aren't valid images
            continue

    return saved