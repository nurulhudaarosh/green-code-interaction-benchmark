import os
import shutil
import tempfile
from pathlib import Path
from PIL import Image

def convert_format(input_dir, output_dir, target_format, background=(255, 255, 255)):
    """
    Convert all images in input_dir to target_format ('PNG' or 'JPEG'),
    writing results to output_dir. Every valid image is re-encoded through
    the pipeline and counted as converted -- including images that are
    already in target_format, since re-encoding (and, for JPEG, flattening
    any transparency) still needs to happen and the file may need to be
    re-saved with consistent settings (e.g. quality, stripped metadata).

    Args:
        input_dir: folder containing source images
        output_dir: folder to write converted images to (created if missing)
        target_format: 'PNG' or 'JPEG' (case-insensitive)
        background: RGB tuple used to flatten transparency for JPEG output
    """
    target_format = target_format.upper()
    if target_format not in ("PNG", "JPEG"):
        raise ValueError("target_format must be 'PNG' or 'JPEG'")

    ext = ".jpg" if target_format == "JPEG" else ".png"

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp"}

    converted, skipped = [], []

    for file in sorted(input_dir.iterdir()):
        if not file.is_file() or file.suffix.lower() not in valid_exts:
            continue

        # NOTE: files already in target_format are NOT skipped here -- they
        # go through the exact same open/flatten/save pipeline below and are
        # counted as converted. This matters both for correctness (a JPEG
        # with an ICC profile or unusual chroma subsampling should still be
        # normalized) and because it's the only way to guarantee any stray
        # alpha/palette-transparency edge cases are handled consistently.
        already_target = file.suffix.lower() == ext

        try:
            with Image.open(file) as img:
                img.load()  # force full read before we ever touch the source path again

                if target_format == "JPEG":
                    if img.mode in ("RGBA", "LA") or (
                        img.mode == "P" and "transparency" in img.info
                    ):
                        img = img.convert("RGBA")
                        flattened = Image.new("RGB", img.size, background)
                        flattened.paste(img, mask=img.split()[-1])
                        img = flattened
                    elif img.mode != "RGB":
                        img = img.convert("RGB")
                else:  # PNG
                    if img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
                        img = img.convert("RGBA")

                out_path = output_dir / (file.stem + ext)
                save_kwargs = {"quality": 95} if target_format == "JPEG" else {}

                # Guard against input_dir == output_dir clobbering a
                # same-named source file mid-write: save to a temp file in
                # the output dir first, then atomically replace.
                fd, tmp_name = tempfile.mkstemp(dir=output_dir, suffix=ext)
                os.close(fd)
                tmp_path = Path(tmp_name)
                try:
                    img.save(tmp_path, format=target_format, **save_kwargs)
                    shutil.move(str(tmp_path), str(out_path))
                except Exception:
                    tmp_path.unlink(missing_ok=True)
                    raise

                converted.append((out_path.name, "re-encoded" if already_target else "converted"))

        except Exception as e:
            skipped.append((file.name, str(e)))

    n_reencoded = sum(1 for _, kind in converted if kind == "re-encoded")
    n_converted = len(converted) - n_reencoded
    print(
        f"Converted {len(converted)} file(s) to {target_format} "
        f"({n_converted} format-converted, {n_reencoded} re-encoded from already-{target_format})."
    )
    if skipped:
        print(f"Skipped {len(skipped)} file(s):")
        for name, err in skipped:
            print(f"  - {name}: {err}")

    return converted, skipped