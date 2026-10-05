import re
from collections import Counter
from typing import Dict, List, Tuple


def analyze_error_log(path: str, top_n: int = 10) -> Dict[str, int]:
    """
    Read a server log file, extract ERROR lines with normalized signatures,
    count them, and return the top-N signatures by frequency.

    Designed for large log files and defensive against edge cases:
      - top_n may exceed the number of distinct signatures (returns all).
      - Files with zero ERROR lines return an empty dict.
      - Ties are broken deterministically: by count descending, then by
        signature ascending (lexicographic), so results are reproducible
        across runs and platforms.

    Normalization replaces variable data (timestamps, IPs, UUIDs, hex values,
    numbers, quoted strings) with placeholders so that similar errors collapse
    into a single signature. Malformed lines (those containing an error keyword
    but failing strict parsing) are tracked under a '<MALFORMED>' signature.

    Args:
        path: Path to the server log file.
        top_n: Number of top signatures to return. Must be a positive integer.
               If it exceeds the number of distinct signatures, all are
               returned. Defaults to 10.

    Returns:
        A dict mapping normalized error signatures to occurrence counts,
        sorted by count descending, then signature ascending, limited to at
        most top_n entries. Empty dict if no ERROR lines are found.

    Raises:
        FileNotFoundError: If the log file does not exist.
        ValueError: If top_n is not a positive integer.
    """
    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n <= 0:
        raise ValueError("top_n must be a positive integer")

    # --- Normalization patterns (order matters: specific → generic) ---
    patterns = [
        (re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-'
                    r'[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'), '<UUID>'),
        (re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'), '<IP>'),
        (re.compile(r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?'
                    r'(?:Z|[+-]\d{2}:?\d{2})?\b'), '<TIMESTAMP>'),
        (re.compile(r'\b\d{2}:\d{2}:\d{2}(?:[.,]\d+)?\b'), '<TIME>'),
        (re.compile(r'\b0x[0-9a-fA-F]+\b'), '<HEX>'),
        (re.compile(r'\b[0-9a-fA-F]{16,}\b'), '<HEX>'),
        (re.compile(r'\b\d+\.\d+\b'), '<FLOAT>'),
        (re.compile(r'\b\d+\b'), '<NUM>'),
        (re.compile(r'"(?:[^"\\]|\\.)*"'), '"<STR>"'),
        (re.compile(r"'(?:[^'\\]|\\.)*'"), "'<STR>'"),
    ]

    # Strict matcher for well-formed ERROR lines.
    error_line_re = re.compile(
        r'^(?:\S+\s+)?'
        r'(?:\[?(?P<level>ERROR|ERR|FATAL|CRITICAL)\]?)'
        r'\b[:\s]*(?P<message>.*)$',
        re.IGNORECASE,
    )

    # Looser check: line mentions an error keyword but didn't strictly parse.
    error_keyword_re = re.compile(r'\b(ERROR|ERR|FATAL|CRITICAL)\b', re.IGNORECASE)

    error_counts: Counter = Counter()
    malformed_count = 0

    def normalize(text: str) -> str:
        text = text.strip()
        for pattern, placeholder in patterns:
            text = pattern.sub(placeholder, text)
        return re.sub(r'\s+', ' ', text)

    try:
        # Stream the file line-by-line; never load it all into memory.
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            in_error_block = False

            for raw_line in f:
                line = raw_line.rstrip('\n')

                if not line.strip():
                    continue

                match = error_line_re.match(line)
                if match:
                    in_error_block = True
                    signature = normalize(match.group('message')) or '<EMPTY>'
                    error_counts[signature] += 1
                    continue

                if in_error_block:
                    stripped = line.strip()
                    if (line.startswith((' ', '\t'))
                            or stripped.lower().startswith(
                                ('caused by', 'traceback', 'at ', 'file '))):
                        signature = normalize(stripped)
                        error_counts[signature] += 1
                        continue
                    in_error_block = False

                if error_keyword_re.search(line):
                    malformed_count += 1

    except FileNotFoundError:
        raise FileNotFoundError(f"Log file not found: {path}")

    if malformed_count:
        error_counts['<MALFORMED>'] = malformed_count

    # Fast path: no errors at all.
    if not error_counts:
        return {}

    # Deterministic ordering: count DESC, then signature ASC.
    # `most_common()` alone is not guaranteed stable for ties, so we sort
    # explicitly. For very large distinct-signature sets we avoid materializing
    # the full sorted list when top_n is smaller than the distinct count by
    # using heapq.nlargest with a compound key.
    if top_n >= len(error_counts):
        ordered: List[Tuple[str, int]] = sorted(
            error_counts.items(), key=lambda kv: (-kv[1], kv[0])
        )
    else:
        import heapq
        # nlargest returns items in order of the key; use (-count, sig) so
        # higher counts come first and ties sort by signature ascending.
        ordered = heapq.nsmallest(
            top_n,
            error_counts.items(),
            key=lambda kv: (-kv[1], kv[0]),
        )

    return dict(ordered)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python analyze_error_log.py <path_to_log> [top_n]")
        sys.exit(1)

    log_path = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    results = analyze_error_log(log_path, top_n=n)
    if not results:
        print("No ERROR lines found.")
    else:
        for signature, count in results.items():
            print(f"{count:>6}  {signature}")