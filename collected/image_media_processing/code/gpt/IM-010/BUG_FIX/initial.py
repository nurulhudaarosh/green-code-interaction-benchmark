import os
from PIL import Image, ImageOps


def rotate_and_crop(input_dir, output_dir, angle_degrees, crop_size):
    """
    Rotate each image in input_dir by angle_degrees, then center-crop
    or pad it to exactly crop_size, and save the results in output_dir.

    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory where processed images are saved.
        angle_degrees (float): Rotation angle in degrees.
        crop_size (tuple): Target size as (width, height).

    Returns:
        None
    """
    os.makedirs(output_dir, exist_ok=True)

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)

        # Skip directories and unsupported files
        if not os.path.isfile(input_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue

        try:
            with Image.open(input_path) as img:
                # Preserve transparency when possible
                if img.mode in ("RGBA", "LA"):
                    fill_color = (0, 0, 0, 0)
                else:
                    img = img.convert("RGB")
                    fill_color = (0, 0, 0)

                # Rotate around the center and expand so the whole
                # rotated image is preserved.
                rotated = img.rotate(
                    angle_degrees,
                    resample=Image.Resampling.BICUBIC,
                    expand=True,
                    fillcolor=fill_color
                )

                target_width, target_height = crop_size

                # Create a target-sized canvas for padding/cropping.
                canvas = Image.new(
                    rotated.mode,
                    (target_width, target_height),
                    fill_color
                )

                # Calculate the centered position.
                x = (target_width - rotated.width) // 2
                y = (target_height - rotated.height) // 2

                # Paste the rotated image at the center.
                canvas.paste(rotated, (x, y), rotated if rotated.mode == "RGBA" else None)

                # If the rotated image is larger than the target,
                # center-crop it.
                left = max(0, (rotated.width - target_width) // 2)
                top = max(0, (rotated.height - target_height) // 2)

                if rotated.width > target_width or rotated.height > target_height:
                    canvas = ImageOps.fit(
                        rotated,
                        (target_width, target_height),
                        method=Image.Resampling.BICUBIC,
                        centering=(0.5, 0.5)
                    )

                output_path = os.path.join(output_dir, filename)
                canvas.save(output_path)

        except Exception as e:
            print(f"Skipping {filename}: {e}")