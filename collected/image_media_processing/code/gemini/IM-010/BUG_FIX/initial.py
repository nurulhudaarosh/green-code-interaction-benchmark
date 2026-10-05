import os
from PIL import Image

def rotate_and_crop(input_dir, output_dir, angle_degrees, crop_size):
    """
    Rotates all images in `input_dir` by `angle_degrees` about their center,
    then center-crops (or pads with black) each image to `crop_size`.
    
    Parameters:
        input_dir (str): Path to directory containing source images.
        output_dir (str): Path to directory where processed images will be saved.
        angle_degrees (float): Angle to rotate images counter-clockwise.
        crop_size (tuple): Target dimensions as (width, height).
    """
    os.makedirs(output_dir, exist_ok=True)
    target_width, target_height = crop_size

    # Valid image extensions to process
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        file_path = os.path.join(input_dir, filename)
        
        with Image.open(file_path) as img:
            # Convert RGBA/P images to RGB if saving to formats like JPEG without alpha
            # Preserve mode or convert as needed
            mode = img.mode
            
            # Rotate image about its center without expanding boundaries
            rotated = img.rotate(angle_degrees, expand=False, resample=Image.BICUBIC)

            # Create target canvas with black/transparent background
            bg_color = (0, 0, 0, 0) if mode == 'RGBA' else (0, 0, 0)
            result = Image.new(mode, (target_width, target_height), bg_color)

            rot_w, rot_h = rotated.size

            # Compute source crop bounds (if rotated image is larger than target)
            src_left = max(0, (rot_w - target_width) // 2)
            src_top = max(0, (rot_h - target_height) // 2)
            src_right = min(rot_w, src_left + target_width)
            src_bottom = min(rot_h, src_top + target_height)

            cropped = rotated.crop((src_left, src_top, src_right, src_bottom))

            # Compute destination paste position (if rotated image is smaller than target)
            dst_left = max(0, (target_width - rot_w) // 2)
            dst_top = max(0, (target_height - rot_h) // 2)

            result.paste(cropped, (dst_left, dst_top))

            # Save processed image
            output_path = os.path.join(output_dir, filename)
            result.save(output_path)

# Example Usage:
# rotate_and_crop("path/to/input", "path/to/output", angle_degrees=45, crop_size=(512, 512))