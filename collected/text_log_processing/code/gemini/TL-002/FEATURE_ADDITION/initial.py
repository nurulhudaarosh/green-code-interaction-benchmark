import csv
import re
import sys
from pathlib import Path

# Matches Common & Combined Log Format:
# 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://..." "Mozilla/..."
LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+)\s+'
    r'(?P<ident>\S+)\s+'
    r'(?P<user>\S+)\s+'
    r'\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<request>[^"]*)"\s+'
    r'(?P<status>\d{3})\s+'
    r'(?P<size>\S+)'
    r'(?:\s+"(?P<referrer>[^"]*)")?'
    r'(?:\s+"(?P<user_agent>[^"]*)")?'
)


def get_status_class(status_code: str) -> str:
    """Returns the HTTP status class (e.g., '2xx', '4xx', '5xx')."""
    if len(status_code) == 3 and status_code[0] in "12345":
        return f"{status_code[0]}xx"
    return "unknown"


def convert_logs_to_csv(input_log_path: str, output_csv_path: str):
    fieldnames = [
        "ip",
        "ident",
        "user",
        "timestamp",
        "method",
        "endpoint",
        "protocol",
        "status",
        "status_class",
        "bytes",
        "referrer",
        "user_agent",
    ]

    parsed_count = 0
    skipped_count = 0

    with open(input_log_path, "r", encoding="utf-8", errors="replace") as log_file, \
         open(output_csv_path, "w", newline="", encoding="utf-8") as csv_file:

        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for line_num, line in enumerate(log_file, 1):
            line = line.strip()
            if not line:
                continue

            match = LOG_PATTERN.match(line)
            if not match:
                skipped_count += 1
                continue

            data = match.groupdict()
            status = data.get("status", "")

            # Split request line into Method, Endpoint, and Protocol
            req_parts = data.get("request", "").split()
            method = req_parts[0] if len(req_parts) > 0 else ""
            endpoint = req_parts[1] if len(req_parts) > 1 else ""
            protocol = req_parts[2] if len(req_parts) > 2 else ""

            # Normalize size ('-' represents 0 in HTTP logs)
            size = data.get("size")
            size_bytes = 0 if size == "-" else size

            row = {
                "ip": data.get("ip"),
                "ident": data.get("ident"),
                "user": data.get("user"),
                "timestamp": data.get("timestamp"),
                "method": method,
                "endpoint": endpoint,
                "protocol": protocol,
                "status": status,
                "status_class": get_status_class(status),
                "bytes": size_bytes,
                "referrer": data.get("referrer") or "",
                "user_agent": data.get("user_agent") or "",
            }

            writer.writerow(row)
            parsed_count += 1

    print(f"Done: {parsed_count} rows exported, {skipped_count} lines skipped.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_logs.py <input.log> <output.csv>")
        sys.exit(1)

    convert_logs_to_csv(sys.argv[1], sys.argv[2])