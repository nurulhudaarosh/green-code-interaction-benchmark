import os
from PIL import Image


def rotate_and_crop(
    input_dir,
    output_dir,
    angle_degrees,
    crop_size,
    fill_color=(0, 0, 0)
):
    """
    Rotate each image and center-crop or center-pad it to exactly crop_size.

    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory where processed images are saved.
        angle_degrees (float): Rotation angle in degrees.
        crop_size (tuple): Target size as (width, height).
        fill_color (tuple): RGB color used for padding. Defaults to black.

    Returns:
        None
    """
    os.makedirs(output_dir, exist_ok=True)

    target_width, target_height = crop_size

    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)

        if not os.path.isfile(input_path):
            continue

        try:
            with Image.open(input_path) as img:
                img = img.convert("RGB")

                # expand=True prevents clipping during rotation
                rotated = img.rotate(
                    angle_degrees,
                    expand=True,
                    resample=Image.Resampling.BICUBIC
                )

                width, height = rotated.size

                # Create target canvas using the specified padding color
                canvas = Image.new(
                    "RGB",
                    (target_width, target_height),
                    fill_color
                )

                # Center-crop if rotated image is larger
                left = max((width - target_width) // 2, 0)
                top = max((height - target_height) // 2, 0)
                right = min(left + target_width, width)
                bottom = min(top + target_height, height)

                cropped = rotated.crop(
                    (left, top, right, bottom)
                )

                # Center the cropped image on the target canvas
                paste_x = (target_width - cropped.width) // 2
                paste_y = (target_height - cropped.height) // 2

                canvas.paste(cropped, (paste_x, paste_y))

                output_path = os.path.join(output_dir, filename)
                canvas.save(output_path)

        except (OSError, ValueError):
            # Skip files that cannot be opened as images
            continue