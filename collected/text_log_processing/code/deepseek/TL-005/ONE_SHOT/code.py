import os
import unicodedata


def normalize_corpus(input_dir, output_dir, lowercase=False):
    """
    Normalize a corpus of .txt files.

    For each .txt file found recursively under input_dir:
      1. Apply Unicode NFC normalization.
      2. Collapse all whitespace runs to a single space, then strip ends.
      3. Optionally lowercase.

    Mirrors the relative directory structure into output_dir.

    Returns a dict:
      {
        "files": [ {"in": ..., "out": ..., "chars_in": int, "chars_out": int}, ... ],
        "total_chars_in": int,
        "total_chars_out": int,
        "per_file": { rel_path: {"chars_in": int, "chars_out": int}, ... }
      }
    """
    files = []
    per_file = {}
    total_chars_in = 0
    total_chars_out = 0

    if not os.path.isdir(input_dir):
        return {
            "files": [],
            "total_chars_in": 0,
            "total_chars_out": 0,
            "per_file": {},
        }

    for root, _dirs, filenames in os.walk(input_dir):
        for name in filenames:
            if not name.lower().endswith(".txt"):
                continue

            in_path = os.path.join(root, name)
            rel_path = os.path.relpath(in_path, input_dir)
            out_path = os.path.join(output_dir, rel_path)

            # Read input (tolerate any encoding oddities gracefully).
            try:
                with open(in_path, "r", encoding="utf-8", errors="replace") as f:
                    raw = f.read()
            except (OSError, IOError):
                continue

            # 1. NFC normalize.
            text = unicodedata.normalize("NFC", raw)

            # 2. Collapse whitespace (any Unicode whitespace -> single space).
            text = " ".join(text.split())

            # 3. Optional lowercase.
            if lowercase:
                text = text.lower()

            # 4. Write output, mirroring directories.
            out_dir = os.path.dirname(out_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)

            chars_in = len(raw)
            chars_out = len(text)
            total_chars_in += chars_in
            total_chars_out += chars_out

            entry = {
                "in": in_path,
                "out": out_path,
                "chars_in": chars_in,
                "chars_out": chars_out,
            }
            files.append(entry)
            per_file[rel_path] = {
                "chars_in": chars_in,
                "chars_out": chars_out,
            }

    files.sort(key=lambda e: e["in"])

    return {
        "files": files,
        "total_chars_in": total_chars_in,
        "total_chars_out": total_chars_out,
        "per_file": per_file,
    }