import re
from collections import Counter


def analyze_error_log(path):
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

            # ERROR exists, but no valid message follows it
            if not match or not match.group(1).strip():
                malformed_lines += 1
                continue

            message = match.group(1).strip()

            # Normalize numbers
            message = re.sub(r"\b\d+\b", "<N>", message)

            # Normalize long hexadecimal IDs
            message = re.sub(r"\b[0-9a-fA-F]{8,}\b", "<ID>", message)

            error_counts[message] += 1

    return dict(error_counts), malformed_lines