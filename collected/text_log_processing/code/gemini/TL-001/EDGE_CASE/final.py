import re
from collections import Counter
from typing import List, Tuple


def analyze_error_log(path: str, top_n: int = 10) -> List[Tuple[str, int]]:
    """Reads a server log file, extracts ERROR lines, normalizes dynamic values,

    and returns up to top_n distinct error signatures.

    Edge cases handled:
    - Files with 0 ERROR lines: returns [] without error.
    - top_n >= number of unique errors: returns all unique errors found.
    - top_n <= 0: returns [] immediately.
    - Tie-breaking: sorted deterministically by frequency descending,
      then by signature alphabetically ascending (-count, signature).
    - Memory efficiency: streams file line-by-line without loading entire file.
    """
    if top_n <= 0:
        return []

    # Regex to capture timestamp and level prefix
    log_pattern = re.compile(
        r"(?:\[?[\d\-T:\.\sZ]+\]?\s+)?(?:\[?(?P<level>[A-Za-z]+)\]?:?\s+)?(?P<message>.*)",
        re.IGNORECASE,
    )

    # Compiled regex patterns for normalizing dynamic entities
    uuid_pattern = re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    )
    ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b")
    hex_pattern = re.compile(r"\b0x[0-9a-fA-F]+\b")
    quoted_pattern = re.compile(r"(['\"]).*?\1")
    num_pattern = re.compile(r"\b\d+\b")
    ws_pattern = re.compile(r"\s+")

    counts = Counter()

    try:
        # Stream file line-by-line with replacement on corrupt byte sequences
        with open(path, "r", encoding="utf-8", errors="replace") as file:
            for line in file:
                line_str = line.strip()
                if not line_str:
                    continue

                # Fast short-circuit string check before running full regex
                line_upper = line_str.upper()
                if "ERROR" not in line_upper and "CRITICAL" not in line_upper:
                    continue

                match = log_pattern.match(line_str)
                if not match:
                    continue

                level = match.group("level")
                message = match.group("message")

                # Verify actual error severity
                is_error = False
                if level and level.upper() in {"ERROR", "CRITICAL"}:
                    is_error = True
                elif "ERROR" in line_upper or "CRITICAL" in line_upper:
                    is_error = True

                if not is_error or not message:
                    continue

                # Normalize dynamic tokens into fixed signature markers
                normalized = uuid_pattern.sub("<UUID>", message)
                normalized = ip_pattern.sub("<IP:PORT>", normalized)
                normalized = hex_pattern.sub("<HEX>", normalized)
                normalized = quoted_pattern.sub("<STR>", normalized)
                normalized = num_pattern.sub("<NUM>", normalized)
                normalized = ws_pattern.sub(" ", normalized).strip()

                if normalized:
                    counts[normalized] += 1

    except (FileNotFoundError, PermissionError) as err:
        print(f"File access error: {err}")
        return []

    # Handle zero errors found
    if not counts:
        return []

    # Deterministic ordering:
    # 1. Primary: Frequency descending (-item[1])
    # 2. Secondary (tie-breaker): Alphabetical ascending (item[0])
    sorted_items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    # If top_n exceeds distinct error count, Python slicing safely returns all items
    return sorted_items[:top_n]