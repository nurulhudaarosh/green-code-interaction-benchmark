import os
import re
import unicodedata


def normalize_corpus(input_dir, output_dir, lowercase=False):
    for root, _, files in os.walk(input_dir):
        # Preserve the complete directory structure.
        rel_dir = os.path.relpath(root, input_dir)
        out_dir = output_dir if rel_dir == "." else os.path.join(output_dir, rel_dir)
        os.makedirs(out_dir, exist_ok=True)

        for name in files:
            if not name.lower().endswith(".txt"):
                continue

            src = os.path.join(root, name)
            dst = os.path.join(out_dir, name)

            with open(src, "r", encoding="utf-8") as f:
                text = f.read()

            # Empty files are valid; normalization simply leaves them empty.
            text = unicodedata.normalize("NFC", text)
            text = re.sub(r"\s+", " ", text).strip()

            if lowercase:
                text = text.lower()

            with open(dst, "w", encoding="utf-8") as f:
                f.write(text)