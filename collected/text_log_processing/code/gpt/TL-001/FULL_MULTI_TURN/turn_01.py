import re
from collections import Counter

def analyze_error_log(path):
    """
    Read a server log file and count ERROR-level entries
    grouped by normalized message.

    Example:
        ERROR Failed to connect to DB: timeout=10
        ERROR Failed to connect to DB: timeout=20

    Both are normalized to:
        Failed to connect to DB: timeout=<N>
    """

    counts = Counter()

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            # Only process ERROR-level log entries
            if "ERROR" not in line:
                continue

            # Extract the message after ERROR
            match = re.search(r"\bERROR\b[:\s-]*(.*)", line)
            if not match:
                continue

            message = match.group(1).strip()

            # Normalize variable values
            message = re.sub(r"\b\d+\b", "<N>", message)
            message = re.sub(r"\b[0-9a-fA-F]{8,}\b", "<ID>", message)

            counts[message] += 1

    return dict(counts)