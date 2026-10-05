#!/usr/bin/env python3
"""Convert Apache/Nginx access logs (common or combined format) to CSV.

Usage: python log2csv.py access.log [output.csv]
Reads stdin if input is "-". Every line is exported; lines that don't match
the format are kept with the raw text in `raw` and statusClass "unknown".
"""
import csv
import re
import sys
from datetime import datetime

LOG_RE = re.compile(
    r'^(?P<ip>\S+) (?P<ident>\S+) (?P<user>\S+) \[(?P<time>[^\]]+)\] '
    r'"(?P<request>.*?)" (?P<status>\d{3}|-) (?P<size>\S+)'
    r'(?: "(?P<referrer>.*?)" "(?P<agent>.*?)")?'
)

FIELDS = ["ip", "ident", "user", "time", "method", "path", "protocol",
          "status", "statusClass", "size", "referrer", "agent", "raw"]


def status_class(status):
    return f"{int(status) // 100}xx" if status.isdigit() else "unknown"


def parse_line(line):
    row = dict.fromkeys(FIELDS, "")
    row["raw"] = line
    row["statusClass"] = "unknown"
    m = LOG_RE.match(line)
    if not m:
        return row
    d = m.groupdict()
    parts = (d["request"] or "").split(" ")
    if len(parts) == 3:
        row["method"], row["path"], row["protocol"] = parts
    else:
        row["path"] = d["request"]
    try:
        row["time"] = datetime.strptime(d["time"], "%d/%b/%Y:%H:%M:%S %z").isoformat()
    except ValueError:
        row["time"] = d["time"]
    row.update(
        ip=d["ip"], ident=d["ident"], user=d["user"],
        status="" if d["status"] == "-" else d["status"],
        statusClass=status_class(d["status"]),
        size="" if d["size"] == "-" else d["size"],
        referrer=d["referrer"] or "", agent=d["agent"] or "",
    )
    return row


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.stdin if sys.argv[1] == "-" else open(sys.argv[1], encoding="utf-8", errors="replace")
    out_path = sys.argv[2] if len(sys.argv) > 2 else "access_log.csv"
    count = 0
    with src, open(out_path, "w", newline="", encoding="utf-8") as out:
        w = csv.DictWriter(out, fieldnames=FIELDS)
        w.writeheader()
        for line in src:
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            w.writerow(parse_line(line))
            count += 1
    print(f"Wrote {count} rows to {out_path}")


if __name__ == "__main__":
    main()