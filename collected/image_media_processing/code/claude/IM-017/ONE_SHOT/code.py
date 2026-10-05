"""Store and retrieve custom string key/value metadata in PNG text chunks.

Pure standard library: the image data is never decoded or re-encoded, so pixels
are preserved bit-for-bit.
"""
import struct
import zlib

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _read_chunks(data):
    """Yield (type, payload) for each chunk of a PNG byte string."""
    if data[:8] != PNG_SIG:
        raise ValueError("Not a valid PNG file")
    pos = 8
    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("Truncated PNG chunk header")
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        payload = data[pos + 8:pos + 8 + length]
        if len(payload) != length:
            raise ValueError("Truncated PNG chunk data")
        crc = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        if zlib.crc32(ctype + payload) != crc:
            raise ValueError(f"CRC mismatch in {ctype!r} chunk")
        yield ctype, payload
        pos += 12 + length


def _make_chunk(ctype, payload):
    crc = zlib.crc32(ctype + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + ctype + payload + struct.pack(">I", crc)


def _validate_key(key):
    if not isinstance(key, str) or not isinstance(key, str):
        raise TypeError("Keys must be strings")
    try:
        raw = key.encode("latin-1")
    except UnicodeEncodeError:
        raise ValueError(f"Key {key!r} must be Latin-1 encodable")
    if not 1 <= len(raw) <= 79:
        raise ValueError(f"Key {key!r} must be 1-79 characters")
    if b"\x00" in raw or key != key.strip():
        raise ValueError(f"Key {key!r} may not contain NUL or leading/trailing spaces")
    return raw


def _text_chunk(key, value):
    """tEXt when the value is Latin-1 safe, otherwise UTF-8 iTXt."""
    if not isinstance(value, str):
        raise TypeError(f"Value for {key!r} must be a string")
    kb = _validate_key(key)
    try:
        vb = value.encode("latin-1")
        if b"\x00" not in vb:
            return _make_chunk(b"tEXt", kb + b"\x00" + vb)
    except UnicodeEncodeError:
        pass
    # iTXt: keyword, NUL, compression flag, method, language tag, NUL, translated kw, NUL, text
    payload = kb + b"\x00" + b"\x00\x00" + b"\x00" + b"\x00" + value.encode("utf-8")
    return _make_chunk(b"iTXt", payload)


def _keyword_of(ctype, payload):
    if ctype in (b"tEXt", b"zTXt", b"iTXt"):
        return payload.split(b"\x00", 1)[0].decode("latin-1")
    return None


def embed_tags(input_path, output_path, tags):
    """Copy a PNG to output_path with `tags` (dict[str, str]) stored as text chunks.

    Existing text chunks with the same keys are replaced; others are kept.
    """
    with open(input_path, "rb") as f:
        data = f.read()

    new_chunks = [_text_chunk(k, v) for k, v in tags.items()]
    replace = set(tags)

    out = [PNG_SIG]
    inserted = False
    for ctype, payload in _read_chunks(data):
        if _keyword_of(ctype, payload) in replace:
            continue  # drop old chunk being overwritten
        if ctype == b"IEND":
            out.extend(new_chunks)
            inserted = True
        out.append(_make_chunk(ctype, payload))
    if not inserted:
        raise ValueError("PNG has no IEND chunk")

    with open(output_path, "wb") as f:
        f.write(b"".join(out))


def read_tags(image_path):
    """Return all text metadata (tEXt, zTXt, iTXt) of a PNG as a dict[str, str]."""
    with open(image_path, "rb") as f:
        data = f.read()

    tags = {}
    for ctype, payload in _read_chunks(data):
        if ctype == b"tEXt":
            key, _, val = payload.partition(b"\x00")
            tags[key.decode("latin-1")] = val.decode("latin-1")
        elif ctype == b"zTXt":
            key, _, rest = payload.partition(b"\x00")
            tags[key.decode("latin-1")] = zlib.decompress(rest[1:]).decode("latin-1")
        elif ctype == b"iTXt":
            key, _, rest = payload.partition(b"\x00")
            flag, method = rest[0], rest[1]
            _, _, rest = rest[2:].partition(b"\x00")   # language tag
            _, _, text = rest.partition(b"\x00")       # translated keyword
            if flag:
                text = zlib.decompress(text)
            tags[key.decode("latin-1")] = text.decode("utf-8")
    return tags


if __name__ == "__main__":
    # Self-test: build a tiny PNG, tag it, read it back, verify pixels untouched.
    def tiny_png():
        raw = b"\x00\xff\x00\x00"  # 1x1 RGB red pixel, filter byte 0
        ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        return (PNG_SIG + _make_chunk(b"IHDR", ihdr)
                + _make_chunk(b"IDAT", zlib.compress(raw)) + _make_chunk(b"IEND", b""))

    import os, tempfile
    d = tempfile.mkdtemp()
    src, dst, dst2 = (os.path.join(d, n) for n in ("a.png", "b.png", "c.png"))
    open(src, "wb").write(tiny_png())

    embed_tags(src, dst, {"author": "Ada", "note": "héllo", "emoji": "snow ❄ 雪"})
    assert read_tags(dst) == {"author": "Ada", "note": "héllo", "emoji": "snow ❄ 雪"}

    embed_tags(dst, dst2, {"author": "Grace"})  # overwrite one key, keep the rest
    got = read_tags(dst2)
    assert got["author"] == "Grace" and got["note"] == "héllo", got

    idat = lambda p: [x for t, x in _read_chunks(open(p, "rb").read()) if t == b"IDAT"]
    assert idat(src) == idat(dst2)
    print("All tests passed:", got)