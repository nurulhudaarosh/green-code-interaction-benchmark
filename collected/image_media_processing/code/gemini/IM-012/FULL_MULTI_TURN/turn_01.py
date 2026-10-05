import os
import cv2
import numpy as np

def letterbox_resize(input_dir, output_dir, target_size=(640, 640), pad_color=(0, 0, 0)):
    """
    Resizes all images in input_dir while maintaining aspect ratio,
    pads them to target_size with content centered, and saves to output_dir.

    :param input_dir: Path to the directory containing input images.
    :param output_dir: Path to the directory where resized images will be saved.
    :param target_size: Tuple (width, height) specifying the output size.
    :param pad_color: Tuple (B, G, R) for the padding color (default: black).
    """
    os.makedirs(output_dir, exist_ok=True)
    target_w, target_h = target_size
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff')

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        img_path = os.path.join(input_dir, filename)
        img = cv2.imread(img_path)

        if img is None:
            print(f"Warning: Could not read image {filename}. Skipping.")
            continue

        h, w = img.shape[:2]

        # Calculate scale factor and new dimensions
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(round(w * scale)), int(round(h * scale))

        # Resize image using area interpolation for downscaling or linear for upscaling
        interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
        resized_img = cv2.resize(img, (new_w, new_h), interpolation=interpolation)

        # Calculate padding to center the image
        pad_w = target_w - new_w
        pad_h = target_h - new_h

        top = pad_h // 2
        bottom = pad_h - top
        left = pad_w // 2
        right = pad_w - left

        # Apply border padding
        letterboxed = cv2.copyMakeBorder(
            resized_img,
            top, bottom, left, right,
            borderType=cv2.BORDER_CONSTANT,
            value=pad_color
        )

        output_path = os.path.join(output_dir, filename)
        cv2.imwrite(output_path, letterboxed)

    print(f"Processing complete. Images saved to: {output_dir}")