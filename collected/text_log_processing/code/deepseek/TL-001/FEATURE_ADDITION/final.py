import re
import json
from collections import Counter
from typing import Dict, Optional, Tuple, Union


def analyze_error_log(
    path: str,
    top_n: Optional[int] = None,
    return_stats: bool = False,
) -> Union[Dict[str, int], Tuple[Dict[str, int], Dict[str, int]]]:
    """
    Read a server log file and return counts of normalized ERROR signatures.

    Normalization strips variable data (timestamps, IPs, numbers, UUIDs, etc.)
    so that similar errors are grouped into a single signature.

    Args:
        path: Path to the log file.
        top_n: If provided, return only the top-N signatures by frequency.
               Must be a positive integer. If None (default), return all.
        return_stats: If True, also return a stats dict containing:
                      - 'total_lines': total lines read
                      - 'error_lines': lines matched as errors
                      - 'continuation_lines': traceback/continuation lines counted
                      - 'malformed_lines': non-empty lines that were neither
                        errors nor valid continuations and could not be parsed
                      - 'blank_lines': empty/whitespace-only lines
                      Returns a tuple (signatures, stats).

    Returns:
        If return_stats is False (default): a dict mapping normalized error
        signatures to their occurrence counts, sorted by count (descending),
        limited to top_n if provided.

        If return_stats is True: a tuple (signatures_dict, stats_dict).

    Raises:
        FileNotFoundError: If the log file does not exist.
        ValueError: If top_n is provided but not a positive integer.
    """
    if top_n is not None and (not isinstance(top_n, int) or top_n <= 0):
        raise ValueError("top_n must be a positive integer or None")

    # Patterns to replace with placeholders during normalization.
    # Order matters: more specific patterns should run first.
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

    # Matches: optional timestamp, level (ERROR/ERR/FATAL/CRITICAL),
    # optional logger/thread info, and the message.
    error_line_re = re.compile(
        r'^(?:\S+\s+)?'                       # optional leading token(s)
        r'(?:\[?(?P<level>ERROR|ERR|FATAL|CRITICAL)\]?)\b'  # level
        r'[:\s]*(?P<message>.*)$',
        re.IGNORECASE,
    )

    # Looser check for lines that clearly contain an error level keyword
    # but don't match the strict pattern above (potential malformed errors).
    error_keyword_re = re.compile(r'\b(ERROR|ERR|FATAL|CRITICAL)\b', re.IGNORECASE)

    error_counts: Counter = Counter()
    stats = {
        'total_lines': 0,
        'error_lines': 0,
        'continuation_lines': 0,
        'malformed_lines': 0,
        'blank_lines': 0,
    }

    def normalize(text: str) -> str:
        text = text.strip()
        for pattern, placeholder in patterns:
            text = pattern.sub(placeholder, text)
        return re.sub(r'\s+', ' ', text)

    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            in_error_block = False

            for raw_line in f:
                stats['total_lines'] += 1
                line = raw_line.rstrip('\n')

                # Blank / whitespace-only lines
                if not line.strip():
                    stats['blank_lines'] += 1
                    continue

                match = error_line_re.match(line)
                if match:
                    in_error_block = True
                    stats['error_lines'] += 1
                    signature = normalize(match.group('message'))
                    error_counts[signature] += 1
                    continue

                if in_error_block:
                    stripped = line.strip()
                    # Continuation lines (indented tracebacks, "Caused by:", etc.)
                    if (line.startswith((' ', '\t'))
                            or stripped.lower().startswith(
                                ('caused by', 'traceback', 'at ', 'file '))):
                        stats['continuation_lines'] += 1
                        signature = normalize(stripped)
                        error_counts[signature] += 1
                        continue
                    else:
                        in_error_block = False

                # Line contains an error keyword but didn't parse strictly —
                # treat as malformed rather than silently ignoring it.
                if error_keyword_re.search(line):
                    stats['malformed_lines'] += 1
                    continue

                # Non-error, non-continuation line (e.g., INFO, DEBUG, WARN).
                # These are valid log lines, not malformed; we simply don't count
                # them as errors.

    except FileNotFoundError:
        raise FileNotFoundError(f"Log file not found: {path}")

    # Sort by count descending, then limit to top_n if requested.
    sorted_items = error_counts.most_common(top_n)
    signatures = dict(sorted_items)

    if return_stats:
        return signatures, stats
    return signatures


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python analyze_error_log.py <path_to_log> [top_n]")
        sys.exit(1)

    log_path = sys.argv[1]
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else None

    signatures, stats = analyze_error_log(log_path, top_n=top_n, return_stats=True)

    print("Top error signatures:")
    for sig, count in signatures.items():
        print(f"{count:>6}  {sig}")

    print("\nStats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")