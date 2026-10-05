from pathlib import Path
import cv2
import numpy as np


def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """Resizes images preserving aspect ratio and pads to target_size, centered.

    Parameters:
        input_dir (str or Path): Path to source directory.
        output_dir (str or Path): Path to output directory.
        target_size (tuple): (target_w, target_h).
        pad_color (tuple): BGR color tuple for padding, defaults to black (0,
          0, 0).
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    target_w, target_h = target_size

    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

    for file_path in input_path.rglob("*"):
        if file_path.suffix.lower() not in valid_exts:
            continue

        img = cv2.imread(str(file_path))
        if img is None:
            continue

        h, w = img.shape[:2]

        # FIX: Compute scale factor using min() to ensure image fits within BOTH dimensions
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(round(w * scale)), int(round(h * scale))

        # Select interpolation based on scale direction
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        resized_img = cv2.resize(img, (new_w, new_h), interpolation=interp)

        # Compute exact symmetric padding to center content
        top = (target_h - new_h) // 2
        bottom = target_h - new_h - top
        left = (target_w - new_w) // 2
        right = target_w - new_w - left

        # Pad remaining space
        letterboxed = cv2.copyMakeBorder(
            resized_img,
            top,
            bottom,
            left,
            right,
            borderType=cv2.BORDER_CONSTANT,
            value=pad_color,
        )

        # Save output preserving relative folder layout
        save_path = output_path / file_path.relative_to(input_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(save_path), letterboxed)