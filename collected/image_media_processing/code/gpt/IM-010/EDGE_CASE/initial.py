from PIL import Image
import os


def rotate_and_crop(input_dir, output_dir, angle_degrees, crop_size):
    """
    Rotate each image in input_dir by angle_degrees, then center-crop or
    center-pad it to exactly crop_size.

    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory to save processed images.
        angle_degrees (float): Rotation angle in degrees.
        crop_size (tuple): Target size as (width, height).

    Returns:
        None
    """
    os.makedirs(output_dir, exist_ok=True)

    target_width, target_height = crop_size

    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)

        # Skip non-files
        if not os.path.isfile(input_path):
            continue

        try:
            with Image.open(input_path) as img:
                # Use RGBA/RGB-compatible processing
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")

                # Rotate with expand=True so corners are not clipped
                rotated = img.rotate(
                    angle_degrees,
                    expand=True,
                    fillcolor=(0, 0, 0)
                )

                # Create target canvas
                if rotated.mode == "RGBA":
                    canvas = Image.new(
                        "RGBA",
                        (target_width, target_height),
                        (0, 0, 0, 0)
                    )
                else:
                    canvas = Image.new(
                        "RGB",
                        (target_width, target_height),
                        (0, 0, 0)
                    )

                # Calculate center crop/pad coordinates
                left = (rotated.width - target_width) // 2
                top = (rotated.height - target_height) // 2
                right = left + target_width
                bottom = top + target_height

                # Crop if rotated image is larger
                crop_left = max(left, 0)
                crop_top = max(top, 0)
                crop_right = min(right, rotated.width)
                crop_bottom = min(bottom, rotated.height)

                cropped = rotated.crop(
                    (crop_left, crop_top, crop_right, crop_bottom)
                )

                # Center position for pasting
                paste_x = max((target_width - cropped.width) // 2, 0)
                paste_y = max((target_height - cropped.height) // 2, 0)

                canvas.paste(cropped, (paste_x, paste_y))

                # Save using the original filename
                output_path = os.path.join(output_dir, filename)
                canvas.save(output_path)

        except Exception as e:
            print(f"Skipping {filename}: {e}")