from collections import Counter
import re
from typing import Dict


def analyze_error_log(path: str) -> Dict[str, int]:
    """Reads a server log file, filters for ERROR entries, normalizes

    dynamic values (UUIDs, timestamps, IPs, hex addresses, numbers),
    and returns a dictionary of signature counts.
    """
    error_counts: Counter[str] = Counter()

    # Pattern to extract the error payload after common log prefixes
    # e.g., "2026-10-04 12:00:00 [ERROR] Connection timed out for user 123"
    error_line_pattern = re.compile(
        r"(?:\[?ERROR\]?[:\s-]+|\bERROR\b[:\s-]+)(.*)", re.IGNORECASE
    )

    # Normalization regexes (applied in sequence)
    uuid_pattern = re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    )
    ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b")
    hex_pattern = re.compile(r"\b0x[0-9a-fA-F]+\b")
    # Date/time patterns within the message body (ISO-8601 or common timestamps)
    timestamp_pattern = re.compile(
        r"\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?\b"
    )
    # Remaining numeric identifiers / IDs / ports
    number_pattern = re.compile(r"\b\d+\b")
    # Collapse multiple whitespaces
    whitespace_pattern = re.compile(r"\s+")

    with open(path, "r", encoding="utf-8", errors="replace") as file:
        for line in file:
            match = error_line_pattern.search(line)
            if not match:
                continue

            msg = match.group(1).strip()

            # Normalize dynamic tokens into generic placeholders
            msg = uuid_pattern.sub("<UUID>", msg)
            msg = ip_pattern.sub("<IP>", msg)
            msg = hex_pattern.sub("<HEX>", msg)
            msg = timestamp_pattern.sub("<TIMESTAMP>", msg)
            msg = number_pattern.sub("<NUM>", msg)
            normalized_signature = whitespace_pattern.sub(" ", msg).strip()

            if normalized_signature:
                error_counts[normalized_signature] += 1

    return dict(error_counts)