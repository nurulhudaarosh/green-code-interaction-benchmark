from pathlib import Path
from PIL import Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}

def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0), align="center"):
    """Resize every image in input_dir to exactly target_size (width, height),
    preserving aspect ratio, placed on a pad_color background.

    align: 'center' (default) or 'top-left' controls where the resized
    content sits within the padded canvas.
    """
    if align not in ("center", "top-left"):
        raise ValueError(f"align must be 'center' or 'top-left', got {align!r}")

    tw, th = target_size
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for path in sorted(Path(input_dir).iterdir()):
        if path.suffix.lower() not in IMAGE_EXTS:
            continue

        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")  # honor camera rotation

            scale = min(tw / im.width, th / im.height)
            nw = max(1, min(tw, round(im.width * scale)))
            nh = max(1, min(th, round(im.height * scale)))
            resized = im.resize((nw, nh), Image.Resampling.LANCZOS)

            if align == "center":
                offset = ((tw - nw) // 2, (th - nh) // 2)
            else:  # 'top-left'
                offset = (0, 0)

            canvas = Image.new("RGB", (tw, th), pad_color)
            canvas.paste(resized, offset)
            canvas.save(out / path.name)