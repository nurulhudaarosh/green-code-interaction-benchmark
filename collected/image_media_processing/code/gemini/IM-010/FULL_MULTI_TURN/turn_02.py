import os
import math
from PIL import Image, ImageOps

def rotate_and_crop(input_dir: str, output_dir: str, angle_degrees: float, crop_size: tuple[int, int]) -> None:
    """
    Rotates all images in input_dir with expand=True (ensuring no corner clipping)
    and center-crops/pads them to exactly crop_size.
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
            
            # Ensure mode supports transparency/rotation without palette conversion issues
            if img.mode == "P":
                img = img.convert("RGBA")

            # Guarantee expand=True behavior by forcing PIL to compute full bounding box
            rotated = img.rotate(angle_degrees, expand=True, resample=Image.BICUBIC)
            
            rot_w, rot_h = rotated.size

            # Set up canvas background (transparent for RGBA, white for RGB)
            is_alpha = rotated.mode in ("RGBA", "LA")
            canvas_mode = "RGBA" if is_alpha else "RGB"
            bg_color = (0, 0, 0, 0) if is_alpha else (255, 255, 255)
            
            canvas = Image.new(canvas_mode, (target_w, target_h), bg_color)

            # Center-crop coordinates from rotated image
            src_left = max(0, (rot_w - target_w) // 2)
            src_top = max(0, (rot_h - target_h) // 2)
            src_right = min(rot_w, src_left + target_w)
            src_bottom = min(rot_h, src_top + target_h)

            cropped = rotated.crop((src_left, src_top, src_right, src_bottom))

            # Center-paste coordinates onto output canvas (for padding if rotated image < crop_size)
            dst_left = max(0, (target_w - cropped.width) // 2)
            dst_top = max(0, (target_h - cropped.height) // 2)

            if cropped.mode in ("RGBA", "LA"):
                canvas.paste(cropped, (dst_left, dst_top), mask=cropped)
            else:
                canvas.paste(cropped, (dst_left, dst_top))

            out_path = os.path.join(output_dir, filename)
            canvas.save(out_path)