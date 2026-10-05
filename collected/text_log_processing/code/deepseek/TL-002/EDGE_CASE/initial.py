#!/usr/bin/env python3
"""
convert_access_log: parse access logs, filter, write CSV, report counts.

Parses Apache/Nginx combined-format access logs and exports them to CSV
with a `statusClass` column (1xx..5xx). Supports filtering by HTTP method
and status class. Returns {'written': n, 'skipped': m}.
"""

import csv
import io
import re
import sys
from datetime import datetime

LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+)\s+'
    r'(?P<ident>\S+)\s+'
    r'(?P<user>\S+)\s+'
    r'\[(?P<time>[^\]]+)\]\s+'
    r'"(?P<request>[^"]*)"\s+'
    r'(?P<status>\d{3})\s+'
    r'(?P<size>\S+)'
    r'(?:\s+"(?P<referer>[^"]*)")?'
    r'(?:\s+"(?P<agent>[^"]*)")?'
)

CSV_FIELDS = [
    "ip", "ident", "user", "time", "method", "path", "protocol",
    "status", "statusClass", "size", "referer", "agent",
]


def _status_class(status: int) -> str:
    return f"{status // 100}xx" if 100 <= status <= 599 else "unknown"


def _parse_timestamp(ts: str) -> str:
    try:
        return datetime.strptime(ts, "%d/%b/%Y:%H:%M:%S %z").isoformat()
    except ValueError:
        return ts


def _parse_line(line: str) -> dict | None:
    m = LOG_PATTERN.match(line.strip())
    if not m:
        return None
    d = m.groupdict()

    request = d.get("request") or ""
    parts = request.split(" ", 2)
    method = parts[0] if len(parts) > 0 else ""
    path = parts[1] if len(parts) > 1 else ""
    protocol = parts[2] if len(parts) > 2 else ""

    try:
        status_int = int(d["status"])
    except (TypeError, ValueError):
        status_int = 0

    return {
        "ip": d["ip"],
        "ident": d["ident"],
        "user": d["user"],
        "time": _parse_timestamp(d["time"]),
        "method": method,
        "path": path,
        "protocol": protocol,
        "status": status_int,
        "statusClass": _status_class(status_int),
        "size": d["size"],
        "referer": d.get("referer") or "",
        "agent": d.get("agent") or "",
    }


def _normalize(values) -> set[str] | None:
    """Upper-case a filter iterable into a set, or None if unset/empty."""
    if not values:
        return None
    return {v.strip().upper() for v in values if v and v.strip()} or None


def convert_access_log(
    input_path,
    output_path,
    *,
    methods=None,
    status_classes=None,
    encoding: str = "utf-8",
    warn_on_invalid: bool = False,
    log_stream=None,
) -> dict:
    """
    Parse an access log, filter rows, write a CSV, and report counts.

    Args:
        input_path: Path to the log file, or '-' for stdin.
        output_path: Path to the CSV file, or '-' for stdout.
        methods: Iterable of HTTP methods to keep (e.g. ["GET", "POST"]).
                 None or empty keeps all.
        status_classes: Iterable of status classes to keep
                        (e.g. ["4xx", "5xx"]). None or empty keeps all.
        encoding: Text encoding for file I/O.
        warn_on_invalid: Emit a warning line for each unparseable log line.
        log_stream: Where to write the summary/warnings. Defaults to stderr.

    Returns:
        {'written': int, 'skipped': int}
    """
    log = log_stream if log_stream is not None else sys.stderr
    method_filter = _normalize(methods)
    class_filter = _normalize(status_classes)

    written = 0
    skipped = 0

    # --- open input ---
    if input_path == "-":
        infile = sys.stdin
        close_in = False
    else:
        infile = open(input_path, "r", encoding=encoding, errors="replace")
        close_in = True

    # --- open output ---
    if output_path == "-":
        outfile = sys.stdout
        close_out = False
    else:
        outfile = open(output_path, "w", encoding=encoding, newline="")
        close_out = True

    try:
        writer = csv.DictWriter(outfile, fieldnames=CSV_FIELDS,
                                extrasaction="ignore")
        writer.writeheader()

        for lineno, line in enumerate(infile, 1):
            if not line.strip():
                continue

            row = _parse_line(line)
            if row is None:
                skipped += 1
                if warn_on_invalid:
                    print(f"Warning: unparseable line {lineno}: "
                          f"{line.rstrip()}", file=log)
                continue

            if method_filter is not None \
                    and row["method"].upper() not in method_filter:
                continue
            if class_filter is not None \
                    and row["statusClass"].upper() not in class_filter:
                continue

            writer.writerow(row)
            written += 1
    finally:
        if close_in:
            infile.close()
        if close_out:
            outfile.close()

    print(f"Wrote {written} rows, skipped {skipped} unparseable lines.",
          file=log)

    return {"written": written, "skipped": skipped}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv=None) -> int:
    import argparse

    p = argparse.ArgumentParser(
        description="Convert access logs to CSV with a statusClass column."
    )
    p.add_argument("input", help="Input log file, or '-' for stdin")
    p.add_argument("output", nargs="?", default="-",
                   help="Output CSV file, or '-' for stdout (default)")
    p.add_argument("--methods", default="",
                   help="Comma-separated HTTP methods to keep (e.g. GET,POST)")
    p.add_argument("--classes", default="",
                   help="Comma-separated status classes to keep (e.g. 4xx,5xx)")
    p.add_argument("--strict", action="store_true",
                   help="Warn on unparseable lines")
    args = p.parse_args(argv)

    methods = [m for m in args.methods.split(",") if m.strip()]
    classes = [c for c in args.classes.split(",") if c.strip()]

    result = convert_access_log(
        args.input,
        args.output,
        methods=methods,
        status_classes=classes,
        warn_on_invalid=args.strict,
    )
    return 0 if result["written"] >= 0 else 1


if __name__ == "__main__":
    sys.exit(_main())