import csv
import re
from typing import Dict, Iterable


def convert_access_log(
    in_path: str,
    out_path: str,
    methods: Iterable[str],
    status_classes: Iterable[str],
) -> Dict[str, int]:
    """Parse an Apache-style access log, filter rows, and stream matching records to CSV.

    Malformed lines and parsing exceptions are skipped and counted in
    'skipped'.
    """
    allowed_methods = {m.strip().upper() for m in methods}
    allowed_status_classes = {sc.strip().lower() for sc in status_classes}

    # Matches: IP, ident, user, [timestamp], "METHOD URL HTTP/...", status, size
    # Handles size as digits, '-', or missing gracefully
    log_pattern = re.compile(
        r"^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+\"([A-Za-z]+)\s+(\S+)(?:\s+[^\"]+)?\"\s+(\d{3})\s+(\d+|-)"
    )

    fieldnames = [
        "ip",
        "timestamp",
        "method",
        "url",
        "status",
        "statusClass",
        "size",
    ]

    written_count = 0
    skipped_count = 0

    with open(in_path, "r", encoding="utf-8", errors="replace") as infile, open(
        out_path, "w", newline="", encoding="utf-8"
    ) as outfile:

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for line in infile:
            try:
                line = line.strip()
                if not line:
                    skipped_count += 1
                    continue

                match = log_pattern.match(line)
                if not match:
                    skipped_count += 1
                    continue

                ip, timestamp, method, url, status, raw_size = match.groups()

                # Normalize fields
                method = method.upper()
                status_class = f"{status[0]}xx".lower()

                # Safely convert size: '-' or invalid values default to 0
                if raw_size == "-" or not raw_size.isdigit():
                    size = 0
                else:
                    size = int(raw_size)

                # Filter check
                if (
                    method not in allowed_methods
                    or status_class not in allowed_status_classes
                ):
                    skipped_count += 1
                    continue

                writer.writerow(
                    {
                        "ip": ip,
                        "timestamp": timestamp,
                        "method": method,
                        "url": url,
                        "status": status,
                        "statusClass": status_class,
                        "size": size,
                    }
                )
                written_count += 1

            except Exception:
                # Catch unexpected encoding, parsing, or conversion errors
                skipped_count += 1
                continue

    return {"written": written_count, "skipped": skipped_count}