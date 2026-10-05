import os
from pathlib import Path
from PIL import Image

def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0),
                     align='center'):
    """
    Resize all images in input_dir preserving aspect ratio, padding to target_size.

    Args:
        input_dir (str): Directory containing input images.
        output_dir (str): Directory to save processed images.
        target_size (tuple): (width, height) of output images.
        pad_color (tuple): RGB tuple for padding. Default (0, 0, 0).
        align (str): Where to place the resized content within the padded canvas.
                     'center'   -> centered both axes (default)
                     'top-left' -> flush to top-left corner (pad on right/bottom)

    Scale factor = min(target_w / src_w, target_h / src_h)  <-- guarantees fit.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_w, target_h = target_size
    if target_w <= 0 or target_h <= 0:
        raise ValueError("target_size must be positive (width, height)")

    # Validate align
    valid_aligns = ('center', 'top-left')
    if align not in valid_aligns:
        raise ValueError(f"align must be one of {valid_aligns}, got {align!r}")

    valid_ext = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tif', '.tiff', '.gif'}

    for img_path in input_dir.iterdir():
        if not img_path.is_file() or img_path.suffix.lower() not in valid_ext:
            continue

        try:
            with Image.open(img_path) as img:
                # Normalize mode
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                elif img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')

                src_w, src_h = img.size
                if src_w == 0 or src_h == 0:
                    print(f"Skipping {img_path}: zero-sized image")
                    continue

                # Correct scale: respect BOTH dimensions
                scale = min(target_w / src_w, target_h / src_h)

                new_w = max(1, int(round(src_w * scale)))
                new_h = max(1, int(round(src_h * scale)))

                # Hard clamp against rounding overflow
                new_w = min(new_w, target_w)
                new_h = min(new_h, target_h)

                resized = img.resize((new_w, new_h), Image.LANCZOS)

                # Build canvas
                if resized.mode == 'L':
                    if isinstance(pad_color, (tuple, list)):
                        pad_val = pad_color[0] if len(pad_color) == 1 else sum(pad_color) // 3
                    else:
                        pad_val = pad_color
                    canvas = Image.new('L', (target_w, target_h), pad_val)
                else:
                    canvas = Image.new('RGB', (target_w, target_h), pad_color)

                # Compute paste position based on align
                if align == 'center':
                    paste_x = (target_w - new_w) // 2
                    paste_y = (target_h - new_h) // 2
                elif align == 'top-left':
                    paste_x = 0
                    paste_y = 0
                else:
                    # Unreachable due to earlier validation, but defensive
                    raise ValueError(f"Unsupported align: {align}")

                canvas.paste(resized, (paste_x, paste_y))

                out_path = output_dir / img_path.name
                save_kwargs = {}
                if out_path.suffix.lower() in ('.jpg', '.jpeg'):
                    save_kwargs['quality'] = 95
                    save_kwargs['subsampling'] = 0
                canvas.save(out_path, **save_kwargs)

        except Exception as e:
            print(f"Failed to process {img_path}: {e}")

    print(f"Done. Processed images saved to {output_dir}")