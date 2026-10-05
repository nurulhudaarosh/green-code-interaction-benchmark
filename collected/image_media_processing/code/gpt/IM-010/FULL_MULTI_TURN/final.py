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
    Rotate each image with expand=True, then center-crop or pad it
    to exactly crop_size.

    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory to save processed images.
        angle_degrees (float): Rotation angle in degrees.
        crop_size (tuple): Target size as (width, height).
        fill_color (tuple): RGB color used for padding.
                           Defaults to black (0, 0, 0).

    Returns:
        None
    """
    os.makedirs(output_dir, exist_ok=True)

    target_width, target_height = crop_size

    if target_width <= 0 or target_height <= 0:
        raise ValueError("crop_size must contain positive dimensions.")

    if (
        not isinstance(fill_color, tuple)
        or len(fill_color) != 3
        or not all(
            isinstance(v, int) and 0 <= v <= 255
            for v in fill_color
        )
    ):
        raise ValueError(
            "fill_color must be an RGB tuple with values from 0 to 255."
        )

    valid_extensions = (
        ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"
    )

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        try:
            with Image.open(input_path) as img:

                # Rotate with expand=True so no content is clipped.
                rotated = img.rotate(
                    angle_degrees,
                    expand=True,
                    fillcolor=fill_color
                )

                rotated_width, rotated_height = rotated.size

                # Create the final image at exactly crop_size.
                # Any unused area remains filled with fill_color.
                result = Image.new(
                    rotated.mode,
                    (target_width, target_height),
                    fill_color
                )

                # Determine the center of the rotated image.
                center_x = rotated_width / 2
                center_y = rotated_height / 2

                # Determine the crop box centered on the rotated image.
                left = int(round(center_x - target_width / 2))
                top = int(round(center_y - target_height / 2))
                right = left + target_width
                bottom = top + target_height

                # Find the part of the crop box that actually overlaps
                # the rotated image.
                src_left = max(left, 0)
                src_top = max(top, 0)
                src_right = min(right, rotated_width)
                src_bottom = min(bottom, rotated_height)

                if src_left < src_right and src_top < src_bottom:
                    cropped = rotated.crop(
                        (src_left, src_top, src_right, src_bottom)
                    )

                    # Position the available image content at the
                    # correct centered location in the final canvas.
                    paste_x = src_left - left
                    paste_y = src_top - top

                    result.paste(
                        cropped,
                        (paste_x, paste_y)
                    )

                result.save(output_path)

        except Exception as e:
            print(f"Error processing {filename}: {e}")