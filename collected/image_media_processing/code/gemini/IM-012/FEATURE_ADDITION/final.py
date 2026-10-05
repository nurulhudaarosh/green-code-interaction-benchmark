from typing import Literal
from pathlib import Path
import cv2
import numpy as np


def letterbox_resize(
    input_dir: str | Path,
    output_dir: str | Path,
    target_size: tuple[int, int],
    pad_color: tuple[int, int, int] = (0, 0, 0),
    align: Literal["center", "top-left"] = "center",
) -> None:
    """Resizes all images in `input_dir` while maintaining aspect ratio, pads

    them to `target_size` (width, height), and saves them to `output_dir`.

    :param align: Positioning of resized content on canvas ('center' or
    'top-left').
    """
    if align not in ("center", "top-left"):
        raise ValueError(
            f"Invalid align option: '{align}'. Expected 'center' or 'top-left'."
        )

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    target_w, target_h = target_size
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

    for img_path in input_path.iterdir():
        if img_path.suffix.lower() not in valid_extensions:
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            continue

        h, w = img.shape[:2]

        # Calculate scale factor preserving aspect ratio
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(round(w * scale)), int(round(h * scale))

        # Resize image using appropriate interpolation method
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        resized_img = cv2.resize(img, (new_w, new_h), interpolation=interp)

        # Compute padding based on alignment
        if align == "center":
            pad_top = (target_h - new_h) // 2
            pad_bottom = target_h - new_h - pad_top
            pad_left = (target_w - new_w) // 2
            pad_right = target_w - new_w - pad_left
        elif align == "top-left":
            pad_top = 0
            pad_bottom = target_h - new_h
            pad_left = 0
            pad_right = target_w - new_w

        # Pad around resized image to reach target dimensions
        padded_img = cv2.copyMakeBorder(
            resized_img,
            top=pad_top,
            bottom=pad_bottom,
            left=pad_left,
            right=pad_right,
            borderType=cv2.BORDER_CONSTANT,
            value=pad_color,  # BGR format by default in OpenCV
        )

        # Save to output directory
        save_path = output_path / img_path.name
        cv2.imwrite(str(save_path), padded_img)


# Example usage:
# letterbox_resize("input_folder", "output_folder", target_size=(640, 640), align="top-left")