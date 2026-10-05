import os
import cv2
import numpy as np
from pathlib import Path


def rotate_and_crop(input_dir, output_dir, angle_degrees, crop_size, fill_color=0):
    """
    Rotate each image in input_dir by angle_degrees and center-crop/pad to crop_size.

    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory to save processed images.
        angle_degrees (float): Rotation angle in degrees (counter-clockwise).
        crop_size (tuple or int): Target size as (width, height) or single int for square.
        fill_color (int, tuple, or list): Fill value for padded regions and rotation
            borders. Scalar for grayscale, or per-channel (B, G, R[, A]).
    """
    if isinstance(crop_size, int):
        crop_w, crop_h = crop_size, crop_size
    else:
        crop_w, crop_h = crop_size

    os.makedirs(output_dir, exist_ok=True)

    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}

    for filename in os.listdir(input_dir):
        src_path = os.path.join(input_dir, filename)
        if not os.path.isfile(src_path):
            continue
        if Path(filename).suffix.lower() not in valid_exts:
            continue

        img = cv2.imread(src_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"Skipping unreadable file: {src_path}")
            continue

        rotated = _rotate_image(img, angle_degrees, fill_color)
        result = _center_crop_or_pad(rotated, crop_w, crop_h, fill_color)

        dst_path = os.path.join(output_dir, filename)
        cv2.imwrite(dst_path, result)


def _resolve_border_value(img, fill_color):
    """Expand fill_color into a tuple matching the image's channel count."""
    channels = img.shape[2] if img.ndim == 3 else 1

    if np.isscalar(fill_color):
        values = [fill_color] * channels
    else:
        values = list(fill_color)
        if len(values) == 1:
            values = values * channels
        elif len(values) < channels:
            # e.g. BGR fill on a BGRA image -> alpha defaults to 255 (opaque)
            if channels == 4 and len(values) == 3:
                values = values + [255]
            else:
                values = values + [values[-1]] * (channels - len(values))
        elif len(values) > channels:
            values = values[:channels]

    if channels == 1:
        return values[0]
    return tuple(values)


def _rotate_image(img, angle_degrees, fill_color):
    """Rotate image about its center, expanding canvas so nothing is clipped."""
    h, w = img.shape[:2]
    center = (w / 2.0, h / 2.0)

    angle_rad = np.deg2rad(angle_degrees)
    cos_a, sin_a = abs(np.cos(angle_rad)), abs(np.sin(angle_rad))
    new_w = int(np.ceil(w * cos_a + h * sin_a))
    new_h = int(np.ceil(w * sin_a + h * cos_a))

    M = cv2.getRotationMatrix2D(center, angle_degrees, 1.0)
    M[0, 2] += (new_w / 2.0) - center[0]
    M[1, 2] += (new_h / 2.0) - center[1]

    border_value = _resolve_border_value(img, fill_color)

    return cv2.warpAffine(
        img, M, (new_w, new_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border_value,
    )


def _center_crop_or_pad(img, target_w, target_h, fill_color):
    """
    Produce an image of exactly (target_w, target_h), centered on the input.

    - If a dimension is larger than the target: center-crop it.
    - If a dimension is smaller than the target: center-pad it with fill_color.
    - If both dimensions are smaller: the entire rotated canvas is placed at
      the center of a (target_w, target_h) canvas filled with fill_color.

    Padding is applied *and* cropping is applied in a single step so the
    center of the input maps to the center of the output in every case.
    """
    h, w = img.shape[:2]
    border_value = _resolve_border_value(img, fill_color)

    # Compute how much of the target lies outside the image, per side.
    # Positive => need to pad that side. Negative => that side gets cropped.
    pad_left = max(0, (target_w - w + 1) // 2)
    pad_right = max(0, (target_w - w) // 2)
    pad_top = max(0, (target_h - h + 1) // 2)
    pad_bottom = max(0, (target_h - h) // 2)

    if pad_left or pad_right or pad_top or pad_bottom:
        if img.ndim == 3:
            img = cv2.copyMakeBorder(
                img, pad_top, pad_bottom, pad_left, pad_right,
                cv2.BORDER_CONSTANT, value=border_value,
            )
        else:
            img = cv2.copyMakeBorder(
                img, pad_top, pad_bottom, pad_left, pad_right,
                cv2.BORDER_CONSTANT, value=border_value,
            )

    # After padding, image is >= target in each dimension. Center-crop.
    h, w = img.shape[:2]
    x = (w - target_w) // 2
    y = (h - target_h) // 2
    return img[y:y + target_h, x:x + target_w]