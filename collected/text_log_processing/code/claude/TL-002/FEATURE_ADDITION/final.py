#!/usr/bin/env python3
"""Convert Apache/Nginx access logs (common or combined format) to CSV.

Usage:
  python log2csv.py access.log [output.csv] [--methods GET,POST] [--status-classes 4xx,5xx]

Reads stdin if input is "-". Without filters every line is exported; lines that
don't match the format are kept with the raw text in `raw` and statusClass
"unknown". With filters, rows that don't match are skipped (use "unknown" in
--status-classes to keep unparseable lines).
"""
import argparse
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


def _norm_methods(methods):
    return {m.strip().upper() for m in methods if m.strip()} or None


def _norm_classes(classes):
    out = set()
    for c in classes:
        c = c.strip().lower()
        if not c:
            continue
        out.add(c if c == "unknown" else f"{c[0]}xx")
    return out or None


def convert(src, out_path, methods=None, status_classes=None):
    """Convert file object `src` to CSV at `out_path`.

    methods: iterable like ["GET", "POST"] (None = all)
    status_classes: iterable like ["4xx", "5xx"] or ["4", "5"] (None = all)
    Returns {'written': n, 'skipped': m}. Blank lines are ignored, not counted.
    """
    methods = _norm_methods(methods or [])
    classes = _norm_classes(status_classes or [])
    written = skipped = 0
    with open(out_path, "w", newline="", encoding="utf-8") as out:
        w = csv.DictWriter(out, fieldnames=FIELDS)
        w.writeheader()
        for line in src:
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            row = parse_line(line)
            if (methods and row["method"].upper() not in methods) or \
               (classes and row["statusClass"] not in classes):
                skipped += 1
                continue
            w.writerow(row)
            written += 1
    return {"written": written, "skipped": skipped}


def main():
    ap = argparse.ArgumentParser(description="Access log to CSV converter")
    ap.add_argument("input", help='log file, or "-" for stdin')
    ap.add_argument("output", nargs="?", default="access_log.csv")
    ap.add_argument("--methods", default="", help="comma-separated, e.g. GET,POST")
    ap.add_argument("--status-classes", default="", help="comma-separated, e.g. 4xx,5xx")
    a = ap.parse_args()

    src = sys.stdin if a.input == "-" else open(a.input, encoding="utf-8", errors="replace")
    with src:
        result = convert(src, a.output, a.methods.split(","), a.status_classes.split(","))
    print(result)


if __name__ == "__main__":
    main()