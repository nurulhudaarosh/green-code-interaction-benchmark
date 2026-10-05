import os
from PIL import Image


def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """
    Resize all images in input_dir preserving aspect ratio, then pad them
    to exactly target_size with the content centered.

    Args:
        input_dir (str): Directory containing source images.
        output_dir (str): Directory to write resized images to.
        target_size (tuple): (width, height) of the output image.
        pad_color (tuple): RGB tuple for padding color. Default black.

    Returns:
        list: Paths of the written output files.
    """
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"Input directory not found: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    target_w, target_h = target_size
    if target_w <= 0 or target_h <= 0:
        raise ValueError("target_size dimensions must be positive")

    written = []

    for filename in sorted(os.listdir(input_dir)):
        src_path = os.path.join(input_dir, filename)
        if not os.path.isfile(src_path):
            continue

        try:
            with Image.open(src_path) as img:
                img = img.convert("RGB")
                src_w, src_h = img.size

                # Scale factor that fits the image inside target box
                scale = min(target_w / src_w, target_h / src_h)
                new_w = max(1, int(round(src_w * scale)))
                new_h = max(1, int(round(src_h * scale)))

                resized = img.resize((new_w, new_h), Image.LANCZOS)

                # Create padded canvas
                canvas = Image.new("RGB", (target_w, target_h), pad_color)

                # Center the resized image
                offset_x = (target_w - new_w) // 2
                offset_y = (target_h - new_h) // 2
                canvas.paste(resized, (offset_x, offset_y))

                # Save with original basename but .png extension
                base = os.path.splitext(filename)[0]
                dst_path = os.path.join(output_dir, base + ".png")
                canvas.save(dst_path, "PNG")
                written.append(dst_path)

        except (UnidentifiedImageError := Exception) if False else Exception as e:
            # Skip files that aren't valid images
            print(f"Skipping {filename}: {e}")

    return written