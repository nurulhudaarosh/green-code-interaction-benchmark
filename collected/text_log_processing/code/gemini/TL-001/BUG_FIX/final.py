import re
from collections import Counter
from typing import Any, Dict


def analyze_error_log(path: str, top_n: int = 10) -> Dict[str, Any]:
    # Matches bracketed timestamp, log level, and the rest of the line
    line_pattern = re.compile(
        r"^\[(?P<timestamp>[^\]\r\n]+)\]\s+(?P<level>[A-Za-z]+)\s*(?P<message>.*)$"
    )
    ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    number_pattern = re.compile(r"\b\d+\b")
    whitespace_pattern = re.compile(r"\s+")

    counts = Counter()
    malformed_count = 0

    with open(path, "r", encoding="utf-8", errors="replace") as file:
        for raw_line in file:
            line_str = raw_line.strip()

            # Blank or whitespace-only lines
            if not line_str:
                malformed_count += 1
                continue

            # Corrupted lines lacking brackets or proper structure
            match = line_pattern.match(line_str)
            if not match:
                malformed_count += 1
                continue

            level = match.group("level").upper()
            message = match.group("message").strip()

            if level == "ERROR":
                # Normalize message
                norm_msg = ip_pattern.sub("<IP>", message)
                norm_msg = number_pattern.sub("<N>", norm_msg)
                norm_msg = whitespace_pattern.sub(" ", norm_msg).strip()

                counts[norm_msg] += 1

    # Sort descending by count, then lexicographically by signature ascending
    sorted_signatures = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    top_entries = [[sig, count] for sig, count in sorted_signatures[:top_n]]

    return {
        "counts": dict(counts),
        "malformed": malformed_count,
        "top": top_entries,
    }