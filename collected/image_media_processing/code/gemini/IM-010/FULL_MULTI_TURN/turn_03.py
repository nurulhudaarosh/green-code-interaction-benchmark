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
    and center-crops/pads them to exactly crop_size.
    
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

            # Determine image mode and fill color format
            is_alpha = img.mode in ("RGBA", "LA")
            bg_color = (*fill_color, 255) if is_alpha else fill_color
            fill_param = bg_color if is_alpha else fill_color

            # Rotate image using expand=True and fill empty rotated corners with fill_color
            rotated = img.rotate(
                angle_degrees, 
                expand=True, 
                resample=Image.BICUBIC, 
                fillcolor=fill_param
            )
            
            rot_w, rot_h = rotated.size

            # Create destination output canvas with fill_color
            canvas_mode = "RGBA" if is_alpha else "RGB"
            canvas = Image.new(canvas_mode, (target_w, target_h), bg_color)

            # Center-crop coordinates from rotated image
            src_left = max(0, (rot_w - target_w) // 2)
            src_top = max(0, (rot_h - target_h) // 2)
            src_right = min(rot_w, src_left + target_w)
            src_bottom = min(rot_h, src_top + target_h)

            cropped = rotated.crop((src_left, src_top, src_right, src_bottom))

            # Center-paste coordinates onto target canvas
            dst_left = max(0, (target_w - cropped.width) // 2)
            dst_top = max(0, (target_h - cropped.height) // 2)

            if cropped.mode in ("RGBA", "LA"):
                canvas.paste(cropped, (dst_left, dst_top), mask=cropped)
            else:
                canvas.paste(cropped, (dst_left, dst_top))

            out_path = os.path.join(output_dir, filename)
            canvas.save(out_path)

if __name__ == "__main__":
    # Example usage with custom fill color (e.g., White padding: (255, 255, 255)):
    rotate_and_crop(
        input_dir="./images_in",
        output_dir="./images_out",
        angle_degrees=45,
        crop_size=(500, 500),
        fill_color=(255, 255, 255)
    )