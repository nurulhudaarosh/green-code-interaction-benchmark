import struct
import zlib


def _create_text_chunk(keyword: str, text: str) -> bytes:
    """Creates a raw PNG tEXt chunk bytes object."""
    # PNG tEXt chunk structure:
    # 4 bytes: Length of Data
    # 4 bytes: Chunk Type ("tEXt")
    # Data: Keyword (ISO 8859-1) + Null separator (0x00) + Text (ISO 8859-1)
    # 4 bytes: CRC32 (over Chunk Type + Data)
    
    keyword_bytes = keyword.encode("latin-1")
    text_bytes = text.encode("latin-1")
    chunk_data = keyword_bytes + b"\x00" + text_bytes
    chunk_type = b"tEXt"
    
    length = len(chunk_data)
    crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
    
    return struct.pack(">I", length) + chunk_type + chunk_data + struct.pack(">I", crc)


def embed_tags(input_path: str, output_path: str, tags: dict[str, str]) -> None:
    """
    Embeds custom key/value string metadata into a PNG file as tEXt chunks.
    Inserts chunks right before the IEND (end of file) chunk.
    """
    with open(input_path, "rb") as f:
        data = f.read()

    # Verify PNG signature
    png_signature = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(png_signature):
        raise ValueError("Provided file is not a valid PNG image.")

    # Locate the IEND chunk (last 12 bytes of a standard PNG)
    iend_pos = data.rfind(b"IEND")
    if iend_pos == -1:
        raise ValueError("Invalid PNG: IEND chunk not found.")
    
    # Back up 4 bytes to account for the IEND length field (which is 0x00000000)
    insert_pos = iend_pos - 4

    # Build metadata bytes
    new_chunks = bytearray()
    for key, value in tags.items():
        new_chunks.extend(_create_text_chunk(key, value))

    # Construct output binary
    output_data = data[:insert_pos] + bytes(new_chunks) + data[insert_pos:]

    with open(output_path, "wb") as f:
        f.write(output_data)


def read_tags(image_path: str) -> dict[str, str]:
    """
    Reads and extracts all tEXt chunk key/value metadata from a PNG file.
    """
    tags = {}
    with open(image_path, "rb") as f:
        png_signature = f.read(8)
        if png_signature != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Provided file is not a valid PNG image.")

        while True:
            # Read chunk length (4 bytes) and chunk type (4 bytes)
            header = f.read(8)
            if len(header) < 8:
                break
            
            length, chunk_type = struct.unpack(">I4s", header)
            chunk_data = f.read(length)
            f.seek(4, 1)  # Skip 4-byte CRC

            if chunk_type == b"tEXt":
                # tEXt format: keyword + null byte + text string
                if b"\x00" in chunk_data:
                    key, val = chunk_data.split(b"\x00", 1)
                    tags[key.decode("latin-1")] = val.decode("latin-1")

            elif chunk_type == b"IEND":
                break

    return tags