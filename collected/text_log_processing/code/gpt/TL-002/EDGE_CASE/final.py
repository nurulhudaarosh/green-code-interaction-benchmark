import re
import csv


def convert_access_log(in_path, out_path, methods, status_classes):
    """
    Parse, filter, and convert an access log to CSV.

    Returns:
        {
            "written": number of CSV data rows written,
            "skipped": number of input rows skipped
        }
    """

    pattern = re.compile(
        r'^(\S+)\s+\S+\s+\S+\s+'
        r'\[([^\]]+)\]\s+'
        r'"(\S+)\s+(\S+)(?:\s+[^"]*)?"\s+'
        r'(\d{3})\s+(\S+)'
    )

    methods = {str(m).upper() for m in (methods or [])}
    status_classes = {str(s).lower() for s in (status_classes or [])}

    written = 0
    skipped = 0

    with open(in_path, "r", encoding="utf-8", errors="replace") as infile, \
         open(out_path, "w", newline="", encoding="utf-8") as outfile:

        writer = csv.writer(outfile)

        # Always write the header, even for an empty input file.
        writer.writerow([
            "ip",
            "timestamp",
            "method",
            "url",
            "status",
            "statusClass",
            "size"
        ])

        for line in infile:
            line = line.strip()

            # Blank/malformed lines
            if not line:
                skipped += 1
                continue

            match = pattern.match(line)

            if not match:
                skipped += 1
                continue

            ip, timestamp, method, url, status, size = match.groups()

            method = method.upper()
            status = int(status)
            status_class = f"{status // 100}xx"

            # Apply filters
            if method not in methods:
                skipped += 1
                continue

            if status_class.lower() not in status_classes:
                skipped += 1
                continue

            # "-" means zero bytes
            if size == "-":
                size = 0
            else:
                try:
                    size = int(size)
                except (ValueError, TypeError):
                    skipped += 1
                    continue

            writer.writerow([
                ip,
                timestamp,
                method,
                url,
                status,
                status_class,
                size
            ])

            written += 1

    return {
        "written": written,
        "skipped": skipped
    }