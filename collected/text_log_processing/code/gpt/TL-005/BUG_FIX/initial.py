import os
import re
import unicodedata


def normalize_corpus(input_dir, output_dir, lowercase=False):
    for root, _, files in os.walk(input_dir):
        for name in files:
            if not name.lower().endswith(".txt"):
                continue

            src = os.path.join(root, name)
            rel_path = os.path.relpath(src, input_dir)
            dst = os.path.join(output_dir, rel_path)

            os.makedirs(os.path.dirname(dst), exist_ok=True)

            with open(src, "r", encoding="utf-8") as f:
                text = f.read()

            text = unicodedata.normalize("NFC", text)
            text = re.sub(r"\s+", " ", text).strip()

            if lowercase:
                text = text.lower()

            with open(dst, "w", encoding="utf-8") as f:
                f.write(text)