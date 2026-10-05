import shutil
from pathlib import Path
from PIL import Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """Resize every image in input_dir to exactly target_size, keeping aspect
    ratio and centering the content on a padded canvas.

    target_size: (width, height), or a single int for a square.
    pad_color:   RGB tuple used for the padding.
    Returns the number of images written.
    """
    if isinstance(target_size, int):
        target_size = (target_size, target_size)
    tw, th = target_size

    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for path in sorted(input_dir.iterdir()):
        if path.suffix.lower() not in IMAGE_EXTS:
            continue

        with Image.open(path) as img:
            # Already exactly target size (and no EXIF rotation to apply):
            # scale is 1.0 and there is no padding, so copy the file as-is.
            # This avoids any resampling, re-encoding, or mode conversion.
            if img.size == (tw, th) and img.getexif().get(0x0112, 1) == 1:
                shutil.copy2(path, output_dir / path.name)
                count += 1
                continue

            img = ImageOps.exif_transpose(img).convert("RGB")
            w, h = img.size

            scale = min(tw / w, th / h)
            nw = min(tw, max(1, round(w * scale)))
            nh = min(th, max(1, round(h * scale)))
            resized = img if (nw, nh) == (w, h) else img.resize((nw, nh), Image.LANCZOS)

            canvas = Image.new("RGB", (tw, th), tuple(pad_color))
            canvas.paste(resized, ((tw - nw) // 2, (th - nh) // 2))
            canvas.save(output_dir / path.name)
            count += 1

    return count