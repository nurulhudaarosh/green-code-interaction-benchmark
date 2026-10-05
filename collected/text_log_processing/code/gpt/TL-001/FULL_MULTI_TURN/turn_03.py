import re
from collections import Counter


def analyze_error_log(path, top_n=None):
    error_counts = Counter()
    malformed_lines = 0

    try:
        file = open(path, "r", encoding="utf-8", errors="replace")
    except OSError:
        raise

    with file:
        for line in file:
            line = line.strip()

            # Skip blank lines
            if not line:
                malformed_lines += 1
                continue

            # Only process ERROR-level entries
            if "ERROR" not in line:
                continue

            match = re.search(r"\bERROR\b[:\s-]*(.*)", line)

            # ERROR exists, but no message follows it
            if not match or not match.group(1).strip():
                malformed_lines += 1
                continue

            message = match.group(1).strip()

            # Normalize numbers
            message = re.sub(r"\b\d+\b", "<N>", message)

            # Normalize long hexadecimal IDs
            message = re.sub(r"\b[0-9a-fA-F]{8,}\b", "<ID>", message)

            error_counts[message] += 1

    # Sort by count descending, then signature alphabetically
    sorted_errors = sorted(
        error_counts.items(),
        key=lambda item: (-item[1], item[0])
    )

    if top_n is not None:
        if top_n < 0:
            raise ValueError("top_n must be non-negative")
        sorted_errors = sorted_errors[:top_n]

    return sorted_errors, malformed_lines