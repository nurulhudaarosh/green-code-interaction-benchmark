import struct
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------------------
# Low-level chunk helpers
# ---------------------------------------------------------------------------

def _make_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Build a PNG chunk: length + type + data + CRC32(type+data)."""
    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return length + chunk_type + data + crc


def _iter_chunks(data: bytes):
    """Yield (chunk_type, chunk_data, raw_chunk_bytes) for a PNG byte string."""
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("Not a valid PNG file (bad signature)")

    pos = len(PNG_SIGNATURE)
    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("Truncated PNG chunk header")
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        chunk_type = data[pos + 4:pos + 8]
        chunk_data = data[pos + 8:pos + 8 + length]
        raw = data[pos:pos + 8 + length + 4]  # include CRC
        yield chunk_type, chunk_data, raw
        pos += 8 + length + 4


def _build_itxt(keyword: str, value: str) -> bytes:
    """
    iTXt chunk layout (PNG spec):
      keyword (1-79 Latin-1) \\0
      compression_flag (1 byte) = 0 (uncompressed)
      compression_method (1 byte) = 0
      language_tag \\0
      translated_keyword \\0
      text (UTF-8)
    """
    kw = keyword.encode("latin-1")
    if not 1 <= len(kw) <= 79:
        raise ValueError(f"iTXt keyword must be 1-79 Latin-1 bytes: {keyword!r}")
    if b"\x00" in kw:
        raise ValueError("Keyword cannot contain a null byte")

    return (
        kw + b"\x00"
        + b"\x00"          # compression flag: uncompressed
        + b"\x00"          # compression method: 0
        + b"" + b"\x00"    # language tag: empty
        + b"" + b"\x00"    # translated keyword: empty
        + value.encode("utf-8")
    )


def _parse_itxt(data: bytes):
    """Parse an iTXt chunk payload into (keyword, value)."""
    kw_end = data.index(b"\x00")
    keyword = data[:kw_end].decode("latin-1")
    rest = data[kw_end + 1:]

    comp_flag, comp_method = rest[0], rest[1]
    rest = rest[2:]

    # skip language tag
    lang_end = rest.index(b"\x00")
    rest = rest[lang_end + 1:]

    # skip translated keyword
    trans_end = rest.index(b"\x00")
    text_bytes = rest[trans_end + 1:]

    if comp_flag:
        if comp_method != 0:
            raise ValueError(f"Unsupported iTXt compression method: {comp_method}")
        text_bytes = zlib.decompress(text_bytes)

    return keyword, text_bytes.decode("utf-8")


def _parse_text(data: bytes):
    """Parse a tEXt chunk payload into (keyword, value)."""
    kw_end = data.index(b"\x00")
    return data[:kw_end].decode("latin-1"), data[kw_end + 1:].decode("latin-1")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def embed_tags(input_path: str, output_path: str, tags: dict) -> None:
    """
    Copy the PNG at `input_path` to `output_path`, embedding each key/value
    pair in `tags` as an iTXt text chunk (UTF-8).

    Existing text chunks with the same keyword are replaced.
    New text chunks are inserted immediately after IHDR (required before IDAT).
    """
    with open(input_path, "rb") as f:
        data = f.read()

    # Normalize tag keys to strings.
    tags = {str(k): str(v) for k, v in tags.items()}

    # Build replacement/new chunks keyed by keyword.
    new_chunks = {k: _make_chunk(b"iTXt", _build_itxt(k, v)) for k, v in tags.items()}

    out = bytearray(PNG_SIGNATURE)
    inserted = False

    for chunk_type, chunk_data, raw in _iter_chunks(data):
        # Drop existing text chunks whose keyword we're overwriting.
        if chunk_type in (b"tEXt", b"iTXt", b"zTXt"):
            try:
                if chunk_type == b"iTXt":
                    kw, _ = _parse_itxt(chunk_data)
                elif chunk_type == b"tEXt":
                    kw, _ = _parse_text(chunk_data)
                else:  # zTXt
                    kw = chunk_data[:chunk_data.index(b"\x00")].decode("latin-1")
            except (ValueError, IndexError):
                kw = None
            if kw in new_chunks:
                continue  # skip; will be re-added below

        out.extend(raw)

        # Insert all new text chunks right after IHDR.
        if chunk_type == b"IHDR" and not inserted:
            for c in new_chunks.values():
                out.extend(c)
            inserted = True

    if not inserted:
        raise ValueError("PNG has no IHDR chunk; file appears corrupt")

    with open(output_path, "wb") as f:
        f.write(out)


def read_tags(image_path: str) -> dict:
    """
    Read all tEXt and iTXt metadata chunks from a PNG and return them
    as a {keyword: value} dict. Later duplicates win.
    """
    with open(image_path, "rb") as f:
        data = f.read()

    tags = {}
    for chunk_type, chunk_data, _ in _iter_chunks(data):
        if chunk_type == b"iTXt":
            try:
                kw, value = _parse_itxt(chunk_data)
                tags[kw] = value
            except (ValueError, IndexError):
                pass  # skip malformed chunk
        elif chunk_type == b"tEXt":
            try:
                kw, value = _parse_text(chunk_data)
                tags[kw] = value
            except (ValueError, IndexError):
                pass
    return tags


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Assume you have a valid PNG named "in.png"
    tags = {
        "Author": "Ada Lovelace",
        "Copyright": "© 2025 — All rights reserved",
        "Description": "A test image with unicode: 日本語 ✓",
        "Software": "embed_tags.py v1.0",
    }

    embed_tags("in.png", "out.png", tags)
    print(read_tags("out.png"))