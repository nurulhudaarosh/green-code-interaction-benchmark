from pathlib import Path
from PIL import Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}

def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """Resize every image in input_dir to exactly target_size (width, height),
    preserving aspect ratio, centered on a pad_color background."""
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

            canvas = Image.new("RGB", (tw, th), pad_color)
            canvas.paste(resized, ((tw - nw) // 2, (th - nh) // 2))
            canvas.save(out / path.name)