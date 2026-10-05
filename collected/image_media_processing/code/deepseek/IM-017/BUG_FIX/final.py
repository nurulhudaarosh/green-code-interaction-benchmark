from PIL import Image


def read_tags(image_path):
    """
    Read all PNG text-chunk metadata as a flat {str: str} dict.

    Uses img.text (the canonical Pillow accessor for tEXt/zTXt/iTXt chunks).
    Falls back to img.info for non-PNG images or older Pillow versions that
    don't populate .text.
    """
    with Image.open(image_path) as img:
        # Preferred: PngImageFile.text holds all decoded text chunks.
        text_chunks = getattr(img, "text", None)
        if text_chunks:
            # img.text values are always str; be defensive anyway.
            return {str(k): str(v) for k, v in text_chunks.items()}

        # Fallback: pick string-valued entries out of info (covers PNGs with
        # no text chunks, and formats where .text isn't defined).
        return {
            k: v for k, v in (img.info or {}).items()
            if isinstance(v, str)
        }