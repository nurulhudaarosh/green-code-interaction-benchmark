import os
from pathlib import Path
from PIL import Image
import numpy as np


def rotate_and_crop(input_dir, output_dir, angle_degrees, crop_size):
    """
    Rotate each image in input_dir by angle_degrees, then center-crop or pad
    to exactly crop_size (width, height).
    
    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory to save processed images.
        angle_degrees (float): Rotation angle in degrees (counter-clockwise).
        crop_size (tuple): Target size as (width, height).
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    target_w, target_h = crop_size
    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
    
    for img_path in sorted(input_dir.iterdir()):
        if not img_path.is_file() or img_path.suffix.lower() not in valid_exts:
            continue
        
        try:
            with Image.open(img_path) as img:
                # Preserve alpha channel if present
                has_alpha = img.mode in ('RGBA', 'LA') or (
                    img.mode == 'P' and 'transparency' in img.info
                )
                working = img.convert('RGBA' if has_alpha else 'RGB')
                
                # Rotate around center; expand=True gives full rotated image,
                # fill with transparent for alpha, black for RGB.
                fill = (0, 0, 0, 0) if has_alpha else (0, 0, 0)
                rotated = working.rotate(
                    angle_degrees,
                    resample=Image.BICUBIC,
                    expand=True,
                    fillcolor=fill,
                )
                
                # Center-crop or pad to exact target size
                result = _center_crop_or_pad(rotated, target_w, target_h, fill)
                
                # Drop alpha if original didn't have it
                if not has_alpha and result.mode == 'RGBA':
                    result = result.convert('RGB')
                
                # Save preserving original format where reasonable
                out_path = output_dir / img_path.name
                save_kwargs = {}
                if img_path.suffix.lower() in ('.jpg', '.jpeg'):
                    save_kwargs['quality'] = 95
                    save_kwargs['subsampling'] = 0
                result.save(out_path, **save_kwargs)
                
        except Exception as e:
            print(f"Failed to process {img_path.name}: {e}")


def _center_crop_or_pad(img, target_w, target_h, fill):
    """Center-crop if larger than target, pad if smaller."""
    w, h = img.size
    
    # Compute source box in original image (may exceed bounds if padding needed)
    left = (w - target_w) // 2
    top = (h - target_h) // 2
    right = left + target_w
    bottom = top + target_h
    
    if w >= target_w and h >= target_h:
        # Pure crop
        return img.crop((left, top, right, bottom))
    
    # Need padding: create canvas and paste the crop region (clipped to img)
    canvas = Image.new(img.mode, (target_w, target_h), fill)
    
    src_left = max(0, left)
    src_top = max(0, top)
    src_right = min(w, right)
    src_bottom = min(h, bottom)
    
    if src_right > src_left and src_bottom > src_top:
        region = img.crop((src_left, src_top, src_right, src_bottom))
        paste_x = src_left - left
        paste_y = src_top - top
        if region.mode == 'RGBA' and canvas.mode == 'RGBA':
            canvas.paste(region, (paste_x, paste_y), region)
        else:
            canvas.paste(region, (paste_x, paste_y))
    
    return canvas


# Example usage
if __name__ == '__main__':
    rotate_and_crop(
        input_dir='./images',
        output_dir='./output',
        angle_degrees=30,
        crop_size=(512, 512),
    )