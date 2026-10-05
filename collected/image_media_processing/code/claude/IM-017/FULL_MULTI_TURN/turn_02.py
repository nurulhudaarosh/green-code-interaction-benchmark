import struct
import zlib

from PIL import Image

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_TEXT_TYPES = (b"tEXt", b"zTXt", b"iTXt")


def _iter_chunks(data):
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("Not a valid PNG file")
    pos = 8
    while pos + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if len(body) != length:
            raise ValueError("Truncated PNG chunk")
        yield ctype, body
        pos += 12 + length


def _make_chunk(ctype, body):
    crc = zlib.crc32(ctype + body) & 0xFFFFFFFF
    return struct.pack(">I", len(body)) + ctype + body + struct.pack(">I", crc)


def _chunk_key(ctype, body):
    """Keyword of a tEXt/zTXt/iTXt chunk (the part before the first NUL)."""
    return body.partition(b"\x00")[0].decode("latin-1")


def _validate(tags):
    for key, value in tags.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("Tag keys and values must be strings")
        if not 1 <= len(key) <= 79:
            raise ValueError(f"Key must be 1-79 characters: {key!r}")
        if key != key.strip() or "\x00" in key:
            raise ValueError(f"Key has leading/trailing spaces or NUL: {key!r}")
        try:
            key.encode("latin-1")
        except UnicodeEncodeError:
            raise ValueError(f"Key must be Latin-1 per the PNG spec: {key!r}")
        if "\x00" in value:
            raise ValueError(f"Value for {key!r} contains a NUL character")


def embed_tags(input_path, output_path, tags):
    """Copy a PNG to output_path with `tags` (dict[str, str]) embedded as iTXt."""
    _validate(tags)
    with open(input_path, "rb") as f:
        data = f.read()

    new_chunks = [
        _make_chunk(b"iTXt", key.encode("latin-1") + b"\x00\x00\x00\x00\x00" + value.encode("utf-8"))
        for key, value in tags.items()
    ]

    out, inserted = [PNG_SIGNATURE], False
    for ctype, body in _iter_chunks(data):
        if ctype in _TEXT_TYPES and _chunk_key(ctype, body) in tags:
            continue  # replaced by the new value
        if ctype == b"IEND":
            out.extend(new_chunks)
            inserted = True
        out.append(_make_chunk(ctype, body))
    if not inserted:
        raise ValueError("PNG has no IEND chunk")

    with open(output_path, "wb") as f:
        f.write(b"".join(out))


def read_tags(image_path):
    """Return all embedded text chunks as a dict[str, str], via Pillow."""
    with Image.open(image_path) as img:
        if img.format != "PNG":
            raise ValueError("Not a PNG image")
        img.load()  # required so text chunks after IDAT are included
        return dict(img.text)