import csv
import re


LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<method>\S+)\s+(?P<url>\S+)(?:\s+[^"]*)?"\s+'
    r'(?P<status>\d{3})\s+(?P<size>\S+)'
)


def convert_access_log(in_path, out_path, methods=None, status_classes=None):
    """
    Parse access logs, apply method/status-class filters,
    and write matching rows to CSV.

    Returns:
        {"written": number_of_written_rows,
         "skipped": number_of_skipped_rows}
    """

    written = 0
    skipped = 0

    # Normalize filters for case-insensitive matching
    methods = {m.upper() for m in methods} if methods else None
    status_classes = {
        s.lower() for s in status_classes
    } if status_classes else None

    with open(in_path, "r", encoding="utf-8") as infile, \
         open(out_path, "w", newline="", encoding="utf-8") as outfile:

        writer = csv.writer(outfile)
        writer.writerow([
            "ip", "timestamp", "method", "url",
            "status", "statusClass", "size"
        ])

        for line in infile:
            line = line.strip()

            if not line:
                skipped += 1
                continue

            match = LOG_PATTERN.match(line)

            if not match:
                skipped += 1
                continue

            data = match.groupdict()

            method = data["method"].upper()

            try:
                status = int(data["status"])
            except (ValueError, TypeError):
                skipped += 1
                continue

            # "-" means missing/unknown size
            if data["size"] == "-":
                size = 0
            else:
                try:
                    size = int(data["size"])
                except (ValueError, TypeError):
                    skipped += 1
                    continue

            status_class = f"{status // 100}xx"

            # Apply method filter
            if methods is not None and method not in methods:
                skipped += 1
                continue

            # Apply status-class filter
            if (
                status_classes is not None
                and status_class.lower() not in status_classes
            ):
                skipped += 1
                continue

            writer.writerow([
                data["ip"],
                data["timestamp"],
                method,
                data["url"],
                status,
                status_class,
                size
            ])

            written += 1

    return {
        "written": written,
        "skipped": skipped
    }