"""Embed and read custom string key/value metadata in PNG text chunks.

Standard library only by default: new chunks are spliced in before IEND, so
the image data stays byte-identical. Passing compress_level to embed_tags
re-encodes the image through Pillow (imported lazily) instead.
Values are stored as iTXt chunks (UTF-8), so any Unicode string works.
"""
import io
import struct
import zlib

PNG_SIG = b"\x89PNG\r\n\x1a\n"
TEXT_TYPES = (b"tEXt", b"zTXt", b"iTXt")


def _chunks(data):
    """Yield (type, payload) for each chunk in a PNG byte string."""
    if data[:8] != PNG_SIG:
        raise ValueError("Not a PNG file")
    pos = 8
    while pos < len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        payload = data[pos + 8:pos + 8 + length]
        if len(payload) != length:
            raise ValueError("Truncated PNG chunk")
        yield ctype, payload
        pos += 12 + length  # length + type + payload + CRC


def _pack(ctype, payload):
    crc = zlib.crc32(ctype + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + ctype + payload + struct.pack(">I", crc)


def _parse_text(ctype, payload):
    """Return (key, value) for a tEXt/zTXt/iTXt payload."""
    key, _, rest = payload.partition(b"\x00")
    key = key.decode("latin-1")
    if ctype == b"tEXt":
        return key, rest.decode("latin-1")
    if ctype == b"zTXt":  # rest = method byte + zlib data
        return key, zlib.decompress(rest[1:]).decode("latin-1")
    flag, _method = rest[0], rest[1]  # iTXt
    _lang, _, rest = rest[2:].partition(b"\x00")
    _trans, _, text = rest.partition(b"\x00")
    if flag:
        text = zlib.decompress(text)
    return key, text.decode("utf-8")


def _check_key(key):
    if not isinstance(key, str):
        raise TypeError("Keys must be strings")
    try:
        raw = key.encode("latin-1")
    except UnicodeEncodeError:
        raise ValueError(f"Key {key!r} must be Latin-1") from None
    if not 1 <= len(raw) <= 79 or key != key.strip() or "\x00" in key:
        raise ValueError(
            f"Invalid key {key!r}: need 1-79 chars, no NULs, no leading/trailing spaces"
        )
    return raw


def _reencode(data, compress_level):
    """Re-save PNG bytes through Pillow with the given zlib compress_level (0-9).

    Pixels are preserved exactly (PNG is lossless). Pillow carries over the ICC
    profile and transparency itself; DPI and EXIF are passed explicitly. Text
    chunks are not copied here: embed_tags handles those separately, so tag
    values never depend on Pillow. Animated PNGs keep only their first frame.
    """
    from PIL import Image

    with Image.open(io.BytesIO(data)) as im:
        im.load()
        kwargs = {"compress_level": compress_level}
        for name in ("dpi", "exif"):
            if im.info.get(name) is not None:
                kwargs[name] = im.info[name]
        buf = io.BytesIO()
        im.save(buf, "PNG", **kwargs)
    return buf.getvalue()


def embed_tags(input_path, output_path, tags, compress_level=None):
    """Copy a PNG to output_path with `tags` (dict[str, str]) stored in iTXt chunks.

    Existing text chunks with the same keys are replaced; all others are kept.

    compress_level: None (default) splices the tags into the original file, so
    the image data is byte-identical. An int 0-9 re-encodes the image through
    Pillow's PNG save with that zlib level (0 = none, 1 = fastest, 9 = smallest).
    Tag values are written by the same code path either way.
    """
    if compress_level is not None and (
        isinstance(compress_level, bool)
        or not isinstance(compress_level, int)
        or not 0 <= compress_level <= 9
    ):
        raise ValueError("compress_level must be None or an integer from 0 to 9")

    new = []
    for key, value in tags.items():
        if not isinstance(value, str):
            raise TypeError(f"Value for {key!r} must be a string")
        payload = _check_key(key) + b"\x00\x00\x00\x00\x00" + value.encode("utf-8")
        new.append(_pack(b"iTXt", payload))

    with open(input_path, "rb") as f:
        data = f.read()

    def keep(ctype, payload):  # text chunks not being replaced
        return ctype in TEXT_TYPES and _parse_text(ctype, payload)[0] not in tags

    original = list(_chunks(data))
    if compress_level is None:
        body = [(t, p) for t, p in original if t not in TEXT_TYPES or keep(t, p)]
    else:
        # Fresh image data from Pillow; carry the original's other text chunks over.
        body = [(t, p) for t, p in _chunks(_reencode(data, compress_level))
                if t not in TEXT_TYPES]
        carried = [(t, p) for t, p in original if keep(t, p)]
        iend = next((i for i, (t, _) in enumerate(body) if t == b"IEND"), len(body))
        body[iend:iend] = carried

    out = [PNG_SIG]
    inserted = False
    for ctype, payload in body:
        if ctype == b"IEND":
            out.extend(new)
            inserted = True
        out.append(_pack(ctype, payload))
    if not inserted:
        raise ValueError("PNG has no IEND chunk")

    with open(output_path, "wb") as f:
        f.write(b"".join(out))


def read_tags(image_path):
    """Return all tEXt/zTXt/iTXt metadata in the PNG as a dict[str, str]."""
    with open(image_path, "rb") as f:
        data = f.read()
    return {
        k: v
        for ctype, payload in _chunks(data)
        if ctype in TEXT_TYPES
        for k, v in [_parse_text(ctype, payload)]
    }