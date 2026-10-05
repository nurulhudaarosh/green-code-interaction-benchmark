import re
from collections import Counter

# Log level token, e.g. "ERROR", "[ERROR]", "ERROR:"
_LEVEL_RE = re.compile(r"\b(TRACE|DEBUG|INFO|NOTICE|WARN(?:ING)?|ERROR|CRITICAL|FATAL)\b")
_ERROR_RE = re.compile(r"\bERROR\b")

# Leading timestamps in common formats
_TS_RE = re.compile(
    r"^\W*("
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
    r"|[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}"
    r"|\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}(?:\s[+-]\d{4})?"
    r")\W*"
)

# Order matters: most specific first
_NORMALIZERS = [
    (re.compile(r"\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b"), "<UUID>"),
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b"), "<IP>"),
    (re.compile(r"\b0x[0-9a-fA-F]+\b"), "<HEX>"),
    (re.compile(r"\b[0-9a-fA-F]{16,}\b"), "<HEX>"),
    (re.compile(r"(?:/[\w.\-]+){2,}"), "<PATH>"),
    (re.compile(r"'[^']*'|\"[^\"]*\""), "<STR>"),
    (re.compile(r"\b\d+(?:\.\d+)?\b"), "<N>"),
]

_CONTINUATION_RE = re.compile(r"^\s+|^(Traceback|Caused by|\.\.\.)")


def _normalize(message):
    for pattern, repl in _NORMALIZERS:
        message = pattern.sub(repl, message)
    return re.sub(r"\s+", " ", message).strip()


def analyze_error_log(path, top_n=10):
    """
    Read a server log, count ERROR lines by normalized signature.

    Returns a dict:
      total_lines, error_lines, malformed_lines, unique_signatures,
      top: [(signature, count), ...] sorted by count desc (top_n entries)
    Malformed = non-blank lines with no log level that aren't stack-trace
    continuations, or ERROR lines with an empty message. Undecodable bytes
    are replaced rather than raising.
    """
    counts = Counter()
    total = errors = malformed = 0

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            total += 1
            line = raw.replace("\x00", "").rstrip("\r\n")
            if not line.strip():
                continue

            m = _ERROR_RE.search(line)
            if not m:
                if not _LEVEL_RE.search(line) and not _CONTINUATION_RE.match(line):
                    malformed += 1
                continue

            message = line[m.end():].lstrip(" :-]\t")
            # Drop bracketed logger/thread prefixes like "[main]" or "[app.db]"
            message = re.sub(r"^(?:\[[^\]]*\]\s*)+", "", message)
            message = _TS_RE.sub("", message)
            signature = _normalize(message)

            if not signature:
                malformed += 1
                continue

            errors += 1
            counts[signature] += 1

    return {
        "total_lines": total,
        "error_lines": errors,
        "malformed_lines": malformed,
        "unique_signatures": len(counts),
        "top": counts.most_common(top_n),
    }


if __name__ == "__main__":
    import sys

    result = analyze_error_log(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10)
    print(f"Lines: {result['total_lines']}  Errors: {result['error_lines']}  "
          f"Malformed: {result['malformed_lines']}  Unique: {result['unique_signatures']}")
    for sig, n in result["top"]:
        print(f"{n:>6}  {sig}")