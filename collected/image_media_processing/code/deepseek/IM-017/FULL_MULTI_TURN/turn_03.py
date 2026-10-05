from PIL import Image
from PIL.PngImagePlugin import PngInfo


def embed_tags(input_path, output_path, tags, compress_level=6):
    """
    Write key/value string tags into PNG text chunks.

    Parameters
    ----------
    input_path : str | Path
        Source PNG.
    output_path : str | Path
        Destination PNG.
    tags : dict
        {keyword: value} pairs. Values are coerced to str.
    compress_level : int, optional
        PNG zlib compression level forwarded to PIL's save().
        0 = no compression (fastest, largest file),
        9 = maximum compression (slowest, smallest file).
        Default 6 (PIL's default). Does not affect tag values.
    """
    if not isinstance(compress_level, int) or not (0 <= compress_level <= 9):
        raise ValueError("compress_level must be an int in 0..9")

    with Image.open(input_path) as img:
        # Preserve existing text chunks, then overlay the new tags.
        meta = PngInfo()
        for k, v in (img.text or {}).items():
            meta.add_text(str(k), str(v))
        for k, v in tags.items():
            meta.add_text(str(k), str(v))

        # 'compress_level' controls IDAT zlib compression only;
        # the PngInfo text chunks are serialized verbatim.
        img.save(output_path, "PNG", pnginfo=meta, compress_level=compress_level)