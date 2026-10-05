import os
from pathlib import Path
from PIL import Image


def rotate_and_crop(input_dir, output_dir, angle_degrees, crop_size, fill_color=(0, 0, 0)):
    """
    Rotate each image in input_dir by angle_degrees and center-crop/pad to crop_size.

    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory to save processed images.
        angle_degrees (float): Rotation angle in degrees (counterclockwise).
        crop_size (tuple): Target size as (width, height).
        fill_color (tuple): RGB tuple (r, g, b) used to fill padding areas
            when the rotated image is smaller than crop_size. Defaults to black.
            Ignored for images with an alpha channel, which are padded
            transparently so the alpha is preserved.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    target_w, target_h = crop_size

    # Validate fill_color up front
    if (not isinstance(fill_color, (tuple, list)) or len(fill_color) != 3
            or not all(isinstance(c, int) and 0 <= c <= 255 for c in fill_color)):
        raise ValueError(
            f"fill_color must be an (r, g, b) tuple of ints in [0, 255], got {fill_color!r}"
        )
    fill_rgb = tuple(fill_color)

    supported_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}

    for img_file in input_path.iterdir():
        if not img_file.is_file() or img_file.suffix.lower() not in supported_exts:
            continue

        try:
            with Image.open(img_file) as img:
                # IMPORTANT: expand=True grows the canvas to fit the entire
                # rotated image, so no corners are clipped before cropping.
                # Do NOT rely on the PIL default (expand=False) — that clips
                # content that falls outside the original bounding box.
                rotated = img.rotate(
                    angle_degrees,
                    resample=Image.BICUBIC,
                    expand=True,
                )

                # Sanity check: after expand=True the rotated image must be
                # at least as large as the original's bounding box.
                assert rotated.size != img.size or angle_degrees % 360 == 0, (
                    f"Rotation of {img_file.name} did not expand the canvas; "
                    "content may have been clipped."
                )

                # Center-crop (or pad if rotated image is smaller than target)
                processed = _center_crop_or_pad(rotated, target_w, target_h, fill_rgb)

                # Save with original format (fallback to PNG for unsupported)
                out_file = output_path / img_file.name
                save_format = img.format if img.format else 'PNG'

                # JPEG doesn't support alpha; convert if needed
                if save_format == 'JPEG' and processed.mode in ('RGBA', 'LA', 'P'):
                    processed = processed.convert('RGB')

                processed.save(out_file, format=save_format)

        except Exception as e:
            print(f"Failed to process {img_file}: {e}")


def _center_crop_or_pad(img, target_w, target_h, fill_rgb=(0, 0, 0)):
    """Center-crop if image is larger than target; pad with fill_rgb if smaller.

    Images with an alpha channel are padded transparently regardless of
    fill_rgb, so their alpha information is preserved.
    """
    w, h = img.size

    if w >= target_w:
        left = (w - target_w) // 2
    else:
        left = -(target_w - w) // 2

    if h >= target_h:
        top = (h - target_h) // 2
    else:
        top = -(target_h - h) // 2

    # Determine fill color based on mode:
    # - Alpha modes: transparent fill so existing alpha is respected
    # - 'L' (grayscale): collapse RGB fill to luminance
    # - 'RGB': use fill_rgb directly
    # - Anything else: convert to RGBA and pad transparently
    if img.mode in ('RGBA', 'LA'):
        bg_color = (0, 0, 0, 0)
        return img.transform(
            (target_w, target_h),
            Image.AFFINE,
            (1, 0, -left, 0, 1, -top),
            resample=Image.BICUBIC,
            fillcolor=bg_color,
        )
    elif img.mode == 'L':
        # Approximate luminance of the requested RGB fill
        r, g, b = fill_rgb
        bg_color = int(round(0.299 * r + 0.587 * g + 0.114 * b))
        return img.transform(
            (target_w, target_h),
            Image.AFFINE,
            (1, 0, -left, 0, 1, -top),
            resample=Image.BICUBIC,
            fillcolor=bg_color,
        )
    elif img.mode == 'RGB':
        return img.transform(
            (target_w, target_h),
            Image.AFFINE,
            (1, 0, -left, 0, 1, -top),
            resample=Image.BICUBIC,
            fillcolor=fill_rgb,
        )
    else:
        # Exotic mode (P, CMYK, etc.): normalize to RGBA and pad transparently
        rgba = img.convert('RGBA')
        return rgba.transform(
            (target_w, target_h),
            Image.AFFINE,
            (1, 0, -left, 0, 1, -top),
            resample=Image.BICUBIC,
            fillcolor=(0, 0, 0, 0),
        )


if __name__ == '__main__':
    # Default black padding
    rotate_and_crop('./images', './output_black', 15.0, (512, 512))

    # White padding
    rotate_and_crop('./images', './output_white', 15.0, (512, 512), fill_color=(255, 255, 255))

    # Mid-gray padding
    rotate_and_crop('./images', './output_gray', 15.0, (512, 512), fill_color=(128, 128, 128))