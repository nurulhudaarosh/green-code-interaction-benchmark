id="58321"
import csv
import re


def convert_access_log(in_path, out_path, methods, status_classes):
    pattern = re.compile(
        r'^(?P<ip>\S+)\s+\S+\s+\S+\s+'
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'"(?P<method>\S+)\s+(?P<url>\S+)(?:\s+[^"]+)?"\s+'
        r'(?P<status>\d{3})\s+(?P<size>\S+)'
    )

    methods = set(methods)
    status_classes = set(status_classes)

    written = 0
    skipped = 0

    with open(in_path, "r", encoding="utf-8", errors="replace") as src, \
         open(out_path, "w", newline="", encoding="utf-8") as dst:

        writer = csv.writer(dst)
        writer.writerow([
            "ip", "timestamp", "method", "url",
            "status", "statusClass", "size"
        ])

        for line in src:
            match = pattern.match(line.strip())

            # Corrupted/malformed line
            if not match:
                skipped += 1
                continue

            data = match.groupdict()

            # Parse status safely
            try:
                status = int(data["status"])
            except (TypeError, ValueError):
                skipped += 1
                continue

            # "-" means zero bytes
            if data["size"] == "-":
                size = 0
            else:
                try:
                    size = int(data["size"])
                except (TypeError, ValueError):
                    skipped += 1
                    continue

            status_class = f"{status // 100}xx"

            # Valid line, but doesn't match the requested filters
            if data["method"] not in methods:
                continue

            if status_class not in status_classes:
                continue

            writer.writerow([
                data["ip"],
                data["timestamp"],
                data["method"],
                data["url"],
                status,
                status_class,
                size,
            ])

            written += 1

    return {
        "written": written,
        "skipped": skipped
    }