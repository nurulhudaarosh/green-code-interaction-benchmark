from pathlib import Path
from PIL import Image


def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """
    Resize images while preserving aspect ratio, then pad them to exactly
    target_size with the content centered.

    Args:
        input_dir: Directory containing input images.
        output_dir: Directory where processed images are saved.
        target_size: Tuple (target_width, target_height).
        pad_color: RGB tuple used for padding. Defaults to black.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_width, target_height = target_size

    for file_path in input_dir.iterdir():
        if not file_path.is_file():
            continue

        try:
            with Image.open(file_path) as img:
                img = img.convert("RGB")

                width, height = img.size

                # Scale so the entire image fits inside target_size
                scale = min(
                    target_width / width,
                    target_height / height
                )

                new_width = max(1, round(width * scale))
                new_height = max(1, round(height * scale))

                resized = img.resize(
                    (new_width, new_height),
                    Image.Resampling.LANCZOS
                )

                # Create target canvas
                canvas = Image.new(
                    "RGB",
                    (target_width, target_height),
                    pad_color
                )

                # Center the resized image
                x = (target_width - new_width) // 2
                y = (target_height - new_height) // 2

                canvas.paste(resized, (x, y))

                # Preserve original filename
                canvas.save(output_dir / file_path.name)

        except (OSError, ValueError):
            # Skip files that are not valid images
            continue