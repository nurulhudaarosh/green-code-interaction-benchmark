#!/usr/bin/env python3
"""
convert_access_log: parse access logs, filter, write CSV, report counts.

Handles edge cases without crashing:
  - Empty input (header-only CSV output, written=0)
  - '-' size values (kept as-is, counted normally)
  - Filters that match nothing (header-only CSV, written=0)
"""

import csv
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

VALID_STATUS_CLASSES = {"1xx", "2xx", "3xx", "4xx", "5xx", "unknown"}


def _status_class(status: int) -> str:
    return f"{status // 100}xx" if 100 <= status <= 599 else "unknown"


def _parse_timestamp(ts: str) -> str:
    try:
        return datetime.strptime(ts, "%d/%b/%Y:%H:%M:%S %z").isoformat()
    except (ValueError, TypeError):
        return ts


def _parse_line(line: str) -> dict | None:
    """Parse one log line. Returns None if it doesn't match. Never raises."""
    try:
        m = LOG_PATTERN.match(line.strip())
    except Exception:
        return None
    if not m:
        return None

    try:
        d = m.groupdict()
        request = d.get("request") or ""
        parts = request.split(" ", 2)
        method = parts[0] if len(parts) > 0 else ""
        path = parts[1] if len(parts) > 1 else ""
        protocol = parts[2] if len(parts) > 2 else ""

        try:
            status_int = int(d.get("status") or 0)
        except (TypeError, ValueError):
            status_int = 0

        # Size may legitimately be '-'; keep as string, never coerce.
        size = d.get("size")
        if size is None:
            size = "-"

        return {
            "ip": d.get("ip") or "",
            "ident": d.get("ident") or "-",
            "user": d.get("user") or "-",
            "time": _parse_timestamp(d.get("time") or ""),
            "method": method,
            "path": path,
            "protocol": protocol,
            "status": status_int,
            "statusClass": _status_class(status_int),
            "size": size,
            "referer": d.get("referer") or "",
            "agent": d.get("agent") or "",
        }
    except Exception:
        return None


def _normalize(values) -> set[str] | None:
    """Upper-case filter into a set, or None if unset/empty/not iterable."""
    if not values:
        return None
    try:
        result = {str(v).strip().upper() for v in values if str(v).strip()}
    except TypeError:
        return None
    return result or None


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

    Always returns {'written': int, 'skipped': int}. Never raises on
    empty input, '-' size values, or filters matching nothing.

    Args:
        input_path: Path to the log file, or '-' for stdin.
        output_path: Path to the CSV file, or '-' for stdout.
        methods: Iterable of HTTP methods to keep. None/empty keeps all.
        status_classes: Iterable of status classes to keep. None/empty keeps all.
        encoding: Text encoding for file I/O.
        warn_on_invalid: Warn on each unparseable log line.
        log_stream: Where to write the summary/warnings. Defaults to stderr.

    Returns:
        {'written': int, 'skipped': int}
    """
    log = log_stream if log_stream is not None else sys.stderr
    method_filter = _normalize(methods)
    class_filter = _normalize(status_classes)

    written = 0
    skipped = 0

    infile = None
    outfile = None
    close_in = False
    close_out = False

    # --- open input (missing file is an error, but we still write a header) ---
    try:
        if input_path == "-":
            infile = sys.stdin
        else:
            infile = open(input_path, "r", encoding=encoding,
                          errors="replace")
            close_in = True
    except OSError as exc:
        # Can't read input: still produce a valid (header-only) CSV.
        infile = None
        print(f"Warning: could not open input '{input_path}': {exc}",
              file=log)

    # --- open output ---
    try:
        if output_path == "-":
            outfile = sys.stdout
        else:
            outfile = open(output_path, "w", encoding=encoding, newline="")
            close_out = True
    except OSError as exc:
        print(f"Error: could not open output '{output_path}': {exc}",
              file=log)
        if close_in and infile is not None:
            infile.close()
        return {"written": 0, "skipped": 0}

    try:
        writer = csv.DictWriter(outfile, fieldnames=CSV_FIELDS,
                                extrasaction="ignore")
        writer.writeheader()

        # If input failed to open, we've already written the header.
        if infile is not None:
            for lineno, line in enumerate(infile, 1):
                # Empty / whitespace-only lines are not counted as skipped.
                if not line or not line.strip():
                    continue

                row = _parse_line(line)
                if row is None:
                    skipped += 1
                    if warn_on_invalid:
                        print(f"Warning: unparseable line {lineno}: "
                              f"{line.rstrip()}", file=log)
                    continue

                # Filters: unset -> None -> keep everything.
                if method_filter is not None \
                        and row["method"].upper() not in method_filter:
                    continue
                if class_filter is not None \
                        and row["statusClass"].upper() not in class_filter:
                    continue

                try:
                    writer.writerow(row)
                except (OSError, ValueError) as exc:
                    # e.g. broken pipe on stdout; stop gracefully.
                    print(f"Warning: stopped writing CSV: {exc}", file=log)
                    break

                written += 1
    finally:
        try:
            if close_in and infile is not None:
                infile.close()
        except OSError:
            pass
        try:
            if close_out and outfile is not None:
                outfile.close()
        except OSError:
            pass

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

    for c in classes:
        if c.strip().lower() not in VALID_STATUS_CLASSES:
            p.error(f"invalid status class '{c}'. "
                    f"Choose from: {', '.join(sorted(VALID_STATUS_CLASSES))}")

    convert_access_log(
        args.input,
        args.output,
        methods=methods,
        status_classes=classes,
        warn_on_invalid=args.strict,
    )
    return 0


if __name__ == "__main__":
    sys.exit(_main())