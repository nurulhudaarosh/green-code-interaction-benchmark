import re
import csv


def convert_access_log(in_path, out_path):
    """
    Convert an access log file to CSV.

    CSV columns:
    ip,timestamp,method,url,status,statusClass,size

    Malformed lines are skipped.
    '-' in the size field is converted to 0.
    """

    # Common/combined Apache/Nginx access-log format
    pattern = re.compile(
        r'^(\S+)\s+\S+\s+\S+\s+'
        r'\[([^\]]+)\]\s+'
        r'"(\S+)\s+(\S+)(?:\s+[^"]*)?"\s+'
        r'(\d{3})\s+'
        r'(\S+)'
    )

    with open(in_path, "r", encoding="utf-8", errors="replace") as infile, \
         open(out_path, "w", newline="", encoding="utf-8") as outfile:

        writer = csv.writer(outfile)

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
                continue

            match = pattern.match(line)

            if not match:
                continue

            ip, timestamp, method, url, status, size = match.groups()

            status = int(status)

            # Convert "-" to 0
            if size == "-":
                size = 0
            else:
                try:
                    size = int(size)
                except ValueError:
                    size = 0

            # Example: 200 -> 2xx, 404 -> 4xx
            status_class = f"{status // 100}xx"

            writer.writerow([
                ip,
                timestamp,
                method,
                url,
                status,
                status_class,
                size
            ])