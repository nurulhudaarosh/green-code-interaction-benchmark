import struct
import zlib
from pathlib import Path


PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def _read_chunks(data):
    """Yield (chunk_type, chunk_data) tuples from PNG bytes."""
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("Not a PNG file (bad signature)")
    pos = 8
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        cdata = data[pos + 8:pos + 8 + length]
        crc = data[pos + 8 + length:pos + 12 + length]
        if zlib.crc32(ctype + cdata) & 0xFFFFFFFF != struct.unpack('>I', crc)[0]:
            raise ValueError(f"CRC mismatch in chunk {ctype!r}")
        yield ctype, cdata
        pos += 12 + length


def _make_chunk(chunk_type, chunk_data):
    """Build a PNG chunk: length + type + data + CRC."""
    return (struct.pack('>I', len(chunk_data)) + chunk_type + chunk_data +
            struct.pack('>I', zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF))


def _encode_text_chunk(keyword, text):
    """Encode a tEXt chunk (Latin-1) unless non-Latin-1, then use iTXt (UTF-8)."""
    try:
        kw = keyword.encode('latin-1')
        txt = text.encode('latin-1')
        if b'\x00' in kw or b'\x00' in txt:
            raise UnicodeEncodeError('latin-1', text, 0, 1, 'NUL not allowed')
        return _make_chunk(b'tEXt', kw + b'\x00' + txt)
    except UnicodeEncodeError:
        # iTXt: keyword\0 comp_flag\0 comp_method\0 lang\0 translated_kw\0 text
        kw = keyword.encode('utf-8')
        txt = text.encode('utf-8')
        body = kw + b'\x00' + b'\x00' + b'\x00' + b'\x00' + b'\x00' + txt
        return _make_chunk(b'iTXt', body)


def _decode_text_chunk(chunk_type, data):
    """Return (keyword, text) from a tEXt, zTXt, or iTXt chunk, else (None, None)."""
    if chunk_type == b'tEXt':
        keyword, _, text = data.partition(b'\x00')
        return keyword.decode('latin-1'), text.decode('latin-1')

    if chunk_type == b'zTXt':
        keyword, _, rest = data.partition(b'\x00')
        if not rest:
            return keyword.decode('latin-1'), ''
        comp_method, compressed = rest[0], rest[1:]
        if comp_method != 0:
            return keyword.decode('latin-1'), ''  # unknown compression
        return keyword.decode('latin-1'), zlib.decompress(compressed).decode('latin-1')

    if chunk_type == b'iTXt':
        parts = data.split(b'\x00', 5)
        if len(parts) < 6:
            return None, None
        keyword, comp_flag, comp_method, _lang, _trans, text = parts
        if comp_flag == b'\x01':
            text = zlib.decompress(text)
        return keyword.decode('utf-8'), text.decode('utf-8')

    return None, None


def embed_tags(input_path, output_path, tags):
    """
    Embed key/value string metadata into PNG text chunks.

    tags: dict of {str: str}. Existing text chunks with matching keywords
    are replaced; other chunks are preserved in their original order.

    Uses tEXt (Latin-1) when possible; falls back to iTXt (UTF-8) otherwise.
    """
    data = Path(input_path).read_bytes()
    tags = {str(k): str(v) for k, v in tags.items()}

    # Parse all chunks (validates signature and CRCs).
    chunks = list(_read_chunks(data))

    # Build new text chunks to insert.
    new_chunks = {k: _encode_text_chunk(k, v) for k, v in tags.items()}

    out = bytearray(PNG_SIGNATURE)
    inserted = False
    for ctype, cdata in chunks:
        if ctype in (b'tEXt', b'zTXt', b'iTXt'):
            kw, _ = _decode_text_chunk(ctype, cdata)
            if kw in tags:
                # Replace: emit the new chunk once, in place of the old one.
                if not inserted:
                    for k in tags:
                        out += new_chunks[k]
                    inserted = True
                continue
            out += _make_chunk(ctype, cdata)
            continue

        # Insert new text chunks right after IHDR if not yet done.
        out += _make_chunk(ctype, cdata)
        if ctype == b'IHDR' and not inserted:
            for k in tags:
                out += new_chunks[k]
            inserted = True

    if not inserted:  # PNG with no IHDR? shouldn't happen, but be safe.
        raise ValueError("Invalid PNG: no IHDR chunk")

    # Write IEND last if not already (we already preserved order, so this is fine).
    Path(output_path).write_bytes(bytes(out))


def read_tags(image_path):
    """Return a dict of {keyword: text} for all tEXt/zTXt/iTXt chunks in the PNG."""
    data = Path(image_path).read_bytes()
    tags = {}
    for ctype, cdata in _read_chunks(data):
        if ctype in (b'tEXt', b'zTXt', b'iTXt'):
            kw, text = _decode_text_chunk(ctype, cdata)
            if kw is not None:
                tags[kw] = text
    return tags