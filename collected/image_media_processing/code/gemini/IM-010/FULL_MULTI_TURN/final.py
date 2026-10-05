import os
from PIL import Image, ImageOps

def rotate_and_crop(
    input_dir: str, 
    output_dir: str, 
    angle_degrees: float, 
    crop_size: tuple[int, int],
    fill_color: tuple[int, int, int] = (0, 0, 0)
) -> None:
    """
    Rotates all images in input_dir with expand=True (ensuring no corner clipping)
    and center-crops/pads them to exactly crop_size using fill_color.
    
    :param input_dir: Path to directory containing source images.
    :param output_dir: Path to directory where processed images will be saved.
    :param angle_degrees: Angle to rotate images counter-clockwise.
    :param crop_size: Tuple (width, height) specifying exact output dimensions.
    :param fill_color: Tuple (R, G, B) specifying background padding color (default black).
    """
    os.makedirs(output_dir, exist_ok=True)
    target_w, target_h = crop_size
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

    for filename in os.listdir(input_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue

        file_path = os.path.join(input_dir, filename)
        
        with Image.open(file_path) as img:
            img = ImageOps.exif_transpose(img)
            
            # Convert palette images to RGBA to ensure proper expansion and rotation
            if img.mode == "P":
                img = img.convert("RGBA")

            # Determine mode and fill color tuple (RGBA vs RGB)
            is_alpha = img.mode in ("RGBA", "LA")
            bg_color = (*fill_color, 255) if is_alpha else fill_color

            # Rotate image with expand=True; empty corners use fill_color
            rotated = img.rotate(
                angle_degrees, 
                expand=True, 
                resample=Image.BICUBIC, 
                fillcolor=bg_color
            )
            
            rot_w, rot_h = rotated.size

            # Create target output canvas filled completely with fill_color
            canvas_mode = "RGBA" if is_alpha else "RGB"
            canvas = Image.new(canvas_mode, (target_w, target_h), bg_color)

            # Crop box calculation:
            # - If rotated canvas > crop_size: center-crops to target_w / target_h
            # - If rotated canvas <= crop_size: captures the full rotated canvas (0 to rot_w / rot_h)
            src_left = max(0, (rot_w - target_w) // 2)
            src_top = max(0, (rot_h - target_h) // 2)
            src_right = min(rot_w, src_left + target_w)
            src_bottom = min(rot_h, src_top + target_h)

            cropped = rotated.crop((src_left, src_top, src_right, src_bottom))

            # Destination paste coordinates on target canvas:
            # - If cropped < crop_size: center-pads on all surrounding sides
            # - If cropped == crop_size: places directly at top-left (0, 0)
            dst_left = (target_w - cropped.width) // 2
            dst_top = (target_h - cropped.height) // 2

            if cropped.mode in ("RGBA", "LA"):
                canvas.paste(cropped, (dst_left, dst_top), mask=cropped)
            else:
                canvas.paste(cropped, (dst_left, dst_top))

            out_path = os.path.join(output_dir, filename)
            canvas.save(out_path)