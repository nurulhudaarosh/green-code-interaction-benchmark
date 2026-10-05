import csv
import re
from typing import Dict, Iterable, Optional, Set, Union

LOG_LINE_PATTERN = re.compile(
    r'^(?P<ip>\S+)\s+'
    r'(?P<ident>\S+)\s+'
    r'(?P<user>\S+)\s+'
    r'\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?:(?P<method>[A-Z]+)\s+(?P<path>\S+)(?:\s+(?P<protocol>[^"]+))?|(?P<raw_request>[^"]*))"\s+'
    r'(?P<status>\d{3})\s+'
    r'(?P<size>\S+)'
    r'(?:\s+"(?P<referer>[^"]*)"\s+"(?P<user_agent>[^"]*)")?'
)


def _safe_int(value: Optional[str], default: int = 0) -> int:
    """Safely cast string to int, handling '-', empty strings, or corrupt tokens."""
    if not value or value == "-":
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def convert_access_log(
    input_log_path: str,
    output_csv_path: str,
    methods: Optional[Union[Iterable[str], str]] = None,
    status_classes: Optional[Union[Iterable[Union[int, str]], int, str]] = None,
) -> Dict[str, int]:
    """Parses a web access log, filters entries, and exports matches to CSV.

    Edge-case protections:
    - Empty file: Outputs CSV containing header row only; all counts 0.
    - Zero matches: Outputs CSV with header row only; 'written' is 0, 'filtered' tracks skips.
    - Size '-': Coerced to 0 (RFC standard for no body bytes sent).
    - Corrupt ints: Protected against ValueError on status/size parsing.
    """
    # Normalize methods: e.g., 'get' -> {'GET'}, ['get', 'post'] -> {'GET', 'POST'}
    allowed_methods: Optional[Set[str]] = None
    if methods is not None:
        if isinstance(methods, str):
            allowed_methods = {methods.strip().upper()}
        else:
            allowed_methods = {str(m).strip().upper() for m in methods if str(m).strip()}

    # Normalize status classes: e.g., 2, '2xx', '200' -> {'2'}
    allowed_classes: Optional[Set[str]] = None
    if status_classes is not None:
        if isinstance(status_classes, (int, str)):
            status_classes = [status_classes]
        allowed_classes = {
            str(sc).strip()[:1]
            for sc in status_classes
            if str(sc).strip() and str(sc).strip()[:1].isdigit()
        }

    csv_fields = [
        "ip",
        "timestamp",
        "method",
        "path",
        "protocol",
        "status",
        "size",
        "referer",
        "user_agent",
    ]

    metrics = {
        "total": 0,
        "written": 0,
        "filtered": 0,
        "malformed": 0,
    }

    # Open files safely with explicit encodings and newline handling
    with open(input_log_path, "r", encoding="utf-8", errors="replace") as in_file, \
         open(output_csv_path, "w", newline="", encoding="utf-8") as out_file:

        writer = csv.DictWriter(out_file, fieldnames=csv_fields)
        # Always write header first: ensures empty files or 0-matches produce a valid CSV schema
        writer.writeheader()

        for line in in_file:
            clean_line = line.strip()
            # Ignore empty blank lines without treating them as malformed
            if not clean_line:
                continue

            metrics["total"] += 1
            match = LOG_LINE_PATTERN.match(clean_line)

            if not match:
                metrics["malformed"] += 1
                continue

            data = match.groupdict()
            method = (data.get("method") or "").upper()
            status_raw = data.get("status") or ""
            status_class = status_raw[:1]

            # 1. Filter by method
            if allowed_methods is not None and method not in allowed_methods:
                metrics["filtered"] += 1
                continue

            # 2. Filter by status code class
            if allowed_classes is not None and status_class not in allowed_classes:
                metrics["filtered"] += 1
                continue

            row = {
                "ip": data.get("ip") or "",
                "timestamp": data.get("timestamp") or "",
                "method": method,
                "path": data.get("path") or "",
                "protocol": data.get("protocol") or "",
                "status": _safe_int(status_raw, default=0),
                "size": _safe_int(data.get("size"), default=0),
                "referer": data.get("referer") or "",
                "user_agent": data.get("user_agent") or "",
            }

            writer.writerow(row)
            metrics["written"] += 1

    return metrics