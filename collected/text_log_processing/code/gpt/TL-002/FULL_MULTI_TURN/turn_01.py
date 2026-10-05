import csv
import re


LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<method>\S+)\s+(?P<url>\S+)(?:\s+[^"]*)?"\s+'
    r'(?P<status>\d{3})\s+(?P<size>\S+)'
)


def convert_access_log(in_path, out_path):
    """
    Parse access log lines and write them to CSV.

    CSV columns:
    ip,timestamp,method,url,status,statusClass,size
    """
    with open(in_path, "r", encoding="utf-8") as infile, \
         open(out_path, "w", newline="", encoding="utf-8") as outfile:

        writer = csv.writer(outfile)
        writer.writerow([
            "ip", "timestamp", "method", "url",
            "status", "statusClass", "size"
        ])

        for line in infile:
            match = LOG_PATTERN.match(line.strip())

            if not match:
                continue

            data = match.groupdict()

            status = int(data["status"])
            data["statusClass"] = f"{status // 100}xx"

            # "-" means no response body size
            data["size"] = 0 if data["size"] == "-" else int(data["size"])

            writer.writerow([
                data["ip"],
                data["timestamp"],
                data["method"],
                data["url"],
                data["status"],
                data["statusClass"],
                data["size"]
            ])