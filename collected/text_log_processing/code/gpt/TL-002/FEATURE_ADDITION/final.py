import re
import csv


def convert_access_log(in_path, out_path, methods, status_classes):
    """
    Convert an access log to CSV with filtering.

    Returns:
        {'written': n, 'skipped': m}

    CSV columns:
        ip,timestamp,method,url,status,statusClass,size
    """

    pattern = re.compile(
        r'^(\S+)\s+\S+\s+\S+\s+'
        r'\[([^\]]+)\]\s+'
        r'"(\S+)\s+(\S+)(?:\s+[^"]*)?"\s+'
        r'(\d{3})\s+'
        r'(\S+)'
    )

    methods = {method.upper() for method in methods}
    status_classes = {
        str(status_class).lower()
        for status_class in status_classes
    }

    written = 0
    skipped = 0

    with open(in_path, "r", encoding="utf-8", errors="replace") as infile, \
         open(out_path, "w", newline="", encoding="utf-8") as outfile:

        writer = csv.writer(outfile)

        # Keep CSV format unchanged
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

            # Convert '-' to 0
            if size == "-":
                size = 0
            else:
                try:
                    size = int(size)
                except ValueError:
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