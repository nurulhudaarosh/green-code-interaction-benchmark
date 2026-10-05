from pathlib import Path
import cv2
import numpy as np


def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """Resizes images from input_dir preserving aspect ratio and pads to target_size.

    Parameters:
        input_dir (str or Path): Path to the source directory containing images.
        output_dir (str or Path): Path to save letterboxed images.
        target_size (tuple): Target dimensions as (target_w, target_h).
        pad_color (tuple): BGR padding color tuple, defaults to black (0, 0, 0).
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    target_w, target_h = target_size

    # Valid image extensions
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

    # Process all images in input_dir
    for file_path in input_path.rglob("*"):
        if file_path.suffix.lower() not in valid_exts:
            continue

        # Load image
        img = cv2.imread(str(file_path))
        if img is None:
            continue

        h, w = img.shape[:2]

        # Calculate scale factor and new dimensions maintaining aspect ratio
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(round(w * scale)), int(round(h * scale))

        # Select interpolation method: Area for downscaling, Linear for upscaling
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        resized_img = cv2.resize(img, (new_w, new_h), interpolation=interp)

        # Calculate padding to center content
        top = (target_h - new_h) // 2
        bottom = target_h - new_h - top
        left = (target_w - new_w) // 2
        right = target_w - new_w - left

        # Add border padding
        letterboxed = cv2.copyMakeBorder(
            resized_img,
            top,
            bottom,
            left,
            right,
            borderType=cv2.BORDER_CONSTANT,
            value=pad_color,
        )

        # Recreate directory structure in output directory
        relative_path = file_path.relative_to(input_path)
        save_path = output_path / relative_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Save processed image
        cv2.imwrite(str(save_path), letterboxed)