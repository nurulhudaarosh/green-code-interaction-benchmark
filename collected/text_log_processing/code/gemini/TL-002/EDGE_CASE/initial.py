import csv
import re
from typing import Dict, Iterable, Optional, Set, Union

# Matches standard Common / Combined Log Format:
# host ident authuser [timestamp] "METHOD path protocol" status bytes ["referer" "user_agent"]
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


def convert_access_log(
    input_log_path: str,
    output_csv_path: str,
    methods: Optional[Union[Iterable[str], str]] = None,
    status_classes: Optional[Union[Iterable[Union[int, str]], int, str]] = None,
) -> Dict[str, int]:
    """Parses a web server access log, filters entries, and exports to CSV.

    Args:
        input_log_path: Path to the raw access log file.
        output_csv_path: Destination path for the converted CSV file.
        methods: HTTP method(s) to retain (e.g., 'GET' or ['GET', 'POST']). Case-insensitive.
                 If None, all methods are retained.
        status_classes: Status code class(es) to retain (e.g., 2 for 2xx, '5xx', [2, 4, 5]).
                        If None, all status codes are retained.

    Returns:
        dict: Summary metrics containing counts for 'written', 'filtered',
              'malformed', and 'total'.
    """
    # Normalize method filter
    allowed_methods: Optional[Set[str]] = None
    if methods is not None:
        if isinstance(methods, str):
            allowed_methods = {methods.upper()}
        else:
            allowed_methods = {m.upper() for m in methods}

    # Normalize status class filter (e.g., 2, '2xx', '200' -> '2')
    allowed_classes: Optional[Set[str]] = None
    if status_classes is not None:
        if isinstance(status_classes, (int, str)):
            status_classes = [status_classes]
        allowed_classes = {str(sc).strip()[:1] for sc in status_classes}

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
        "written": 0,
        "filtered": 0,
        "malformed": 0,
        "total": 0,
    }

    with open(input_log_path, "r", encoding="utf-8", errors="replace") as in_file, \
         open(output_csv_path, "w", newline="", encoding="utf-8") as out_file:

        writer = csv.DictWriter(out_file, fieldnames=csv_fields)
        writer.writeheader()

        for line in in_file:
            clean_line = line.strip()
            if not clean_line:
                continue

            metrics["total"] += 1
            match = LOG_LINE_PATTERN.match(clean_line)

            if not match:
                metrics["malformed"] += 1
                continue

            data = match.groupdict()
            method = (data.get("method") or "").upper()
            status = data.get("status", "")
            status_class = status[:1]

            # Apply method filter
            if allowed_methods is not None and method not in allowed_methods:
                metrics["filtered"] += 1
                continue

            # Apply status class filter
            if allowed_classes is not None and status_class not in allowed_classes:
                metrics["filtered"] += 1
                continue

            # Standardize missing/dash sizes
            size_val = 0 if data["size"] == "-" else int(data["size"])

            row = {
                "ip": data["ip"],
                "timestamp": data["timestamp"],
                "method": method,
                "path": data.get("path") or "",
                "protocol": data.get("protocol") or "",
                "status": int(status),
                "size": size_val,
                "referer": data.get("referer") or "",
                "user_agent": data.get("user_agent") or "",
            }

            writer.writerow(row)
            metrics["written"] += 1

    return metrics