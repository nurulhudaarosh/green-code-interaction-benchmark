import re
from collections import Counter

# Matches the ERROR level token in common formats:
#   2026-10-04 12:00:00,123 ERROR [db] msg
#   [ERROR] msg   |   level=ERROR msg   |   <timestamp> - ERROR - msg
_LEVEL_RE = re.compile(r"(?:^|[\s\[(=|])ERROR(?:[\s\])|:\-]|$)")

# Normalization rules, applied in order (specific patterns before generic numbers).
_NORMALIZERS = [
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "<UUID>"),
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b"), "<IP>"),
    (re.compile(r"\b0x[0-9a-fA-F]+\b"), "<HEX>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"), "<TS>"),
    (re.compile(r"(?<![\w/])/(?:[\w.\-]+/)+[\w.\-]*"), "<PATH>"),
    (re.compile(r"\"[^\"]*\"|'[^']*'"), "<STR>"),
    (re.compile(r"\b\d+(?:\.\d+)?\b"), "<N>"),
]


def _normalize(message: str) -> str:
    for pattern, repl in _NORMALIZERS:
        message = pattern.sub(repl, message)
    return re.sub(r"\s+", " ", message).strip()


def analyze_error_log(path, top_n=None):
    """Return (top, malformed).

    top:       list of (normalized_message, count) sorted by count descending,
               ties broken by message ascending (fully deterministic).
               - empty file or no ERROR lines  -> []
               - top_n None                    -> all signatures
               - top_n == 0                    -> []
               - top_n > distinct signatures   -> all signatures (no padding)
    malformed: number of lines skipped (blank, corrupted, or ERROR with no
               message). A completely empty (0-byte) file yields 0.
    """
    if top_n is not None:
        if isinstance(top_n, bool) or not isinstance(top_n, int):
            raise TypeError("top_n must be an int or None")
        if top_n < 0:
            raise ValueError("top_n must be >= 0 or None")

    counts = Counter()
    malformed = 0

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        while True:
            try:
                line = f.readline()
            except Exception:
                malformed += 1
                break  # unreadable stream: stop instead of looping forever
            if line == "":  # EOF (also immediately true for an empty file)
                break

            try:
                if not line.strip() or "\x00" in line or "\ufffd" in line:
                    malformed += 1
                    continue

                m = _LEVEL_RE.search(line)
                if not m:
                    continue  # valid line, just not ERROR level

                message = re.sub(r"^[\s:\-|\]]+", "", line[m.end():].strip())
                if not message:
                    malformed += 1  # ERROR level but no message
                    continue

                counts[_normalize(message)] += 1
            except Exception:
                malformed += 1

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    top = ranked if top_n is None else ranked[:top_n]  # slicing is safe if top_n is too large
    return top, malformed


if __name__ == "__main__":
    import sys

    path = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else None
    top, malformed = analyze_error_log(path, top_n=n)
    if not top:
        print("No ERROR entries found.")
    for msg, c in top:
        print(f"{c:6d}  {msg}")
    print(f"\nMalformed lines skipped: {malformed}")