import os
from pathlib import Path
from PIL import Image


def rotate_and_crop(input_dir, output_dir, angle_degrees, crop_size):
    """
    Rotate each image in input_dir by angle_degrees and center-crop/pad to crop_size.
    
    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory to save processed images.
        angle_degrees (float): Rotation angle in degrees (counterclockwise).
        crop_size (tuple): Target size as (width, height).
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    target_w, target_h = crop_size
    
    supported_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
    
    for img_file in input_path.iterdir():
        if not img_file.is_file() or img_file.suffix.lower() not in supported_exts:
            continue
        
        try:
            with Image.open(img_file) as img:
                # Rotate with expand=True so corners aren't cut off
                # Use bicubic for quality; preserve transparency for RGBA
                rotated = img.rotate(
                    angle_degrees,
                    resample=Image.BICUBIC,
                    expand=True,
                )
                
                # Center-crop (or pad if rotated image is smaller than target)
                processed = _center_crop_or_pad(rotated, target_w, target_h)
                
                # Save with original format (fallback to PNG for unsupported)
                out_file = output_path / img_file.name
                save_format = img.format if img.format else 'PNG'
                
                # JPEG doesn't support alpha; convert if needed
                if save_format == 'JPEG' and processed.mode in ('RGBA', 'LA', 'P'):
                    processed = processed.convert('RGB')
                
                processed.save(out_file, format=save_format)
                
        except Exception as e:
            print(f"Failed to process {img_file}: {e}")


def _center_crop_or_pad(img, target_w, target_h):
    """Center-crop if image is larger than target; pad with transparent/black if smaller."""
    w, h = img.size
    
    # Determine if we need to crop or pad
    if w >= target_w:
        # Crop width
        left = (w - target_w) // 2
        right = left + target_w
    else:
        # Pad width
        left = -(target_w - w) // 2
        right = left + target_w
    
    if h >= target_h:
        top = (h - target_h) // 2
        bottom = top + target_h
    else:
        top = -(target_h - h) // 2
        bottom = top + target_h
    
    # Choose background color: transparent for images with alpha, black otherwise
    if img.mode in ('RGBA', 'LA'):
        bg_color = (0, 0, 0, 0)
    elif img.mode == 'RGB':
        bg_color = (0, 0, 0)
    elif img.mode == 'L':
        bg_color = 0
    else:
        bg_color = None
    
    # Use transform to crop/pad in one operation
    if bg_color is not None:
        return img.transform(
            (target_w, target_h),
            Image.AFFINE,
            (1, 0, -left, 0, 1, -top),
            resample=Image.BICUBIC,
            fillcolor=bg_color,
        )
    else:
        # For exotic modes, convert to RGBA for padding
        rgba = img.convert('RGBA')
        return rgba.transform(
            (target_w, target_h),
            Image.AFFINE,
            (1, 0, -left, 0, 1, -top),
            resample=Image.BICUBIC,
            fillcolor=(0, 0, 0, 0),
        )


# Example usage
if __name__ == '__main__':
    rotate_and_crop(
        input_dir='./images',
        output_dir='./output',
        angle_degrees=15.0,
        crop_size=(512, 512),
    )