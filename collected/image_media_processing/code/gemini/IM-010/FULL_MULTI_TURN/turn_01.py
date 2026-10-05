import os
from PIL import Image, ImageOps

def rotate_and_crop(input_dir: str, output_dir: str, angle_degrees: float, crop_size: tuple[int, int]) -> None:
    """
    Rotates all images in input_dir and center-crops/pads them to exactly crop_size.
    
    :param input_dir: Path to directory containing source images.
    :param output_dir: Path to directory where processed images will be saved.
    :param angle_degrees: Angle to rotate images counter-clockwise.
    :param crop_size: Tuple (width, height) specifying exact output dimensions.
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
            # Maintain orientation from EXIF metadata if present
            img = ImageOps.exif_transpose(img)
            
            # Rotate image with expansion to keep rotated corners intact
            # expand=True changes canvas size to fit rotated bounds
            rotated = img.rotate(angle_degrees, expand=True, resample=Image.BICUBIC)
            
            rot_w, rot_h = rotated.size

            # Create destination canvas (RGBA for PNG to preserve transparency, RGB otherwise)
            is_alpha = rotated.mode in ("RGBA", "LA") or (rotated.mode == "P" and "transparency" in rotated.info)
            canvas_mode = "RGBA" if is_alpha else "RGB"
            bg_color = (0, 0, 0, 0) if is_alpha else (255, 255, 255)
            
            canvas = Image.new(canvas_mode, (target_w, target_h), bg_color)

            # Calculate source crop box (center of rotated image)
            src_left = max(0, (rot_w - target_w) // 2)
            src_top = max(0, (rot_h - target_h) // 2)
            src_right = min(rot_w, src_left + target_w)
            src_bottom = min(rot_h, src_top + target_h)

            cropped = rotated.crop((src_left, src_top, src_right, src_bottom))

            # Calculate destination paste coordinates (center of output canvas)
            dst_left = max(0, (target_w - rot_w) // 2)
            dst_top = max(0, (target_h - rot_h) // 2)

            # Paste cropped image onto the centered target canvas
            if cropped.mode in ("RGBA", "LA"):
                canvas.paste(cropped, (dst_left, dst_top), mask=cropped)
            else:
                canvas.paste(cropped, (dst_left, dst_top))

            # Save processed image
            out_path = os.path.join(output_dir, filename)
            canvas.save(out_path)

if __name__ == "__main__":
    # Example usage:
    # Rotate by 45 degrees and make every image exactly 500x500
    rotate_and_crop(
        input_dir="./images_in",
        output_dir="./images_out",
        angle_degrees=45,
        crop_size=(500, 500)
    )