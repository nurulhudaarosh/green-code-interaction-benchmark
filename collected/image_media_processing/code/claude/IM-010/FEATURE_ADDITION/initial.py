from pathlib import Path
from typing import Tuple, Union

from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


def rotate_and_crop(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    angle_degrees: float,
    crop_size: Union[int, Tuple[int, int]],
) -> int:
    """Rotate every image in input_dir, then center-crop/pad to exactly crop_size.

    Args:
        input_dir: Folder containing images (non-recursive).
        output_dir: Folder to write results to (created if missing).
        angle_degrees: Counter-clockwise rotation angle.
        crop_size: (width, height) tuple, or a single int for a square.

    Returns:
        Number of images processed.

    Notes:
        - The canvas is expanded on rotation so no content is lost before cropping.
        - If the rotated image is larger than crop_size in a dimension it is
          center-cropped; if smaller, it is centered and padded (transparent for
          images with alpha, black otherwise).
    """
    if isinstance(crop_size, int):
        crop_size = (crop_size, crop_size)
    cw, ch = crop_size
    if cw <= 0 or ch <= 0:
        raise ValueError("crop_size must be positive")

    input_dir, output_dir = Path(input_dir), Path(output_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(input_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue

        with Image.open(path) as img:
            img.load()
            # Normalize palette / exotic modes so fill and rotation behave.
            if img.mode == "P" or img.mode not in ("L", "RGB", "RGBA", "LA"):
                has_alpha = "transparency" in img.info or "A" in img.getbands()
                img = img.convert("RGBA" if has_alpha else "RGB")

            fill = (0,) * len(img.getbands())  # black, or transparent if alpha
            rotated = img.rotate(
                angle_degrees,
                resample=Image.BICUBIC,
                expand=True,
                fillcolor=fill,
            )

            # One paste handles both cropping (negative offset) and padding.
            canvas = Image.new(rotated.mode, (cw, ch), fill)
            offset = ((cw - rotated.width) // 2, (ch - rotated.height) // 2)
            canvas.paste(rotated, offset)

            # JPEG can't store alpha.
            if path.suffix.lower() in {".jpg", ".jpeg"} and canvas.mode in ("RGBA", "LA"):
                canvas = canvas.convert("RGB")

            canvas.save(output_dir / path.name)
            count += 1

    return count


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Rotate and center-crop/pad images.")
    p.add_argument("input_dir")
    p.add_argument("output_dir")
    p.add_argument("angle", type=float, help="degrees, counter-clockwise")
    p.add_argument("width", type=int)
    p.add_argument("height", type=int, nargs="?", help="defaults to width")
    a = p.parse_args()

    n = rotate_and_crop(a.input_dir, a.output_dir, a.angle, (a.width, a.height or a.width))
    print(f"Processed {n} image(s).")