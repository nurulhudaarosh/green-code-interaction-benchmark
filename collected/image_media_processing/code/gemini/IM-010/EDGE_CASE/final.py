import os
from PIL import Image

def rotate_and_crop(
    input_dir: str, 
    output_dir: str, 
    angle_degrees: float, 
    crop_size: tuple[int, int],
    fill_color: tuple[int, ...] | str = (0, 0, 0)
) -> None:
    """
    Rotates images in input_dir, then center-crops or pads them onto a canvas of exactly crop_size.

    :param input_dir: Path to directory containing source images.
    :param output_dir: Path to directory where processed images will be saved.
    :param angle_degrees: Counter-clockwise rotation angle in degrees.
    :param crop_size: Target dimensions as a (width, height) tuple.
    :param fill_color: Color used to pad canvas when crop_size exceeds rotated image dimensions.
    """
    os.makedirs(output_dir, exist_ok=True)
    crop_w, crop_h = crop_size
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff')

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        file_path = os.path.join(input_dir, filename)
        
        with Image.open(file_path) as img:
            # Determine canvas mode based on input image capabilities
            has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
            canvas_mode = "RGBA" if has_alpha else "RGB"
            
            # Rotate image with expanded boundaries
            img_converted = img.convert(canvas_mode)
            rotated = img_converted.rotate(angle_degrees, expand=True, resample=Image.BICUBIC)
            rot_w, rot_h = rotated.size

            # Create destination canvas initialized to fill_color
            canvas = Image.new(canvas_mode, (crop_w, crop_h), fill_color)

            # Compute paste offsets (where top-left of rotated image should go relative to canvas)
            paste_x = (crop_w - rot_w) // 2
            paste_y = (crop_h - rot_h) // 2

            if paste_x >= 0 and paste_y >= 0:
                # Rotated canvas fits completely inside crop_size (padded on all sides)
                mask = rotated.split()[-1] if canvas_mode == "RGBA" else None
                canvas.paste(rotated, (paste_x, paste_y), mask=mask)
            else:
                # Rotated canvas is larger in one or both dimensions (crop required)
                crop_left = max(0, -paste_x)
                crop_top = max(0, -paste_y)
                crop_right = min(rot_w, crop_left + crop_w)
                crop_bottom = min(rot_h, crop_top + crop_h)

                cropped_part = rotated.crop((crop_left, crop_top, crop_right, crop_bottom))
                
                # Compute paste destination on canvas for the cropped piece
                dest_x = max(0, paste_x)
                dest_y = max(0, paste_y)
                mask = cropped_part.split()[-1] if canvas_mode == "RGBA" else None
                canvas.paste(cropped_part, (dest_x, dest_y), mask=mask)

            # Convert JPEG files or requested RGB formats back to RGB mode
            save_path = os.path.join(output_dir, filename)
            if filename.lower().endswith(('.jpg', '.jpeg')) and canvas.mode == "RGBA":
                rgb_canvas = Image.new("RGB", (crop_w, crop_h), fill_color if isinstance(fill_color, tuple) else (255, 255, 255))
                rgb_canvas.paste(canvas, mask=canvas.split()[3])
                rgb_canvas.save(save_path)
            else:
                canvas.save(save_path)