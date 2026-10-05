from PIL import Image
import os


def rotate_and_crop(input_dir, output_dir, angle_degrees, crop_size, fill_color=(0, 0, 0)):
    """
    Rotate each image, then center-crop or center-pad it to exactly crop_size.

    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory to save processed images.
        angle_degrees (float): Rotation angle in degrees.
        crop_size (tuple): Target size as (width, height).
        fill_color (tuple): RGB color used for padding. Default is black.

    Returns:
        None
    """
    os.makedirs(output_dir, exist_ok=True)

    target_width, target_height = crop_size

    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)

        # Skip directories and other non-file entries
        if not os.path.isfile(input_path):
            continue

        try:
            with Image.open(input_path) as img:
                # Convert to RGB for consistent fill_color handling
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Rotate with expand=True so no content is clipped
                rotated = img.rotate(
                    angle_degrees,
                    expand=True,
                    fillcolor=fill_color
                )

                # Create the final canvas at exactly crop_size.
                # This also provides padding when crop_size is larger
                # than the rotated image.
                canvas = Image.new(
                    "RGB",
                    (target_width, target_height),
                    fill_color
                )

                # Determine the region of the rotated image that
                # will actually be copied.
                src_left = max((rotated.width - target_width) // 2, 0)
                src_top = max((rotated.height - target_height) // 2, 0)

                src_right = min(
                    src_left + target_width,
                    rotated.width
                )
                src_bottom = min(
                    src_top + target_height,
                    rotated.height
                )

                cropped = rotated.crop(
                    (src_left, src_top, src_right, src_bottom)
                )

                # Center the cropped portion on the target canvas.
                paste_x = (target_width - cropped.width) // 2
                paste_y = (target_height - cropped.height) // 2

                canvas.paste(cropped, (paste_x, paste_y))

                # Save with the original filename
                output_path = os.path.join(output_dir, filename)
                canvas.save(output_path)

        except Exception as e:
            print(f"Skipping {filename}: {e}")