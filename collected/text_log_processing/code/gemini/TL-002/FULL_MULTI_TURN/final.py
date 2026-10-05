import csv
import re
from typing import Dict, Iterable, Optional, Set, Union

LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+)\s+'
    r'(?P<ident>\S+)\s+'
    r'(?P<auth>\S+)\s+'
    r'\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<request>[^"]*)"\s+'
    r'(?P<status>\d{3})\s+'
    r'(?P<size>\S+)'
    r'(?:\s+"(?P<referer>[^"]*)")?'
    r'(?:\s+"(?P<user_agent>[^"]*)")?'
)


def safe_int(value: Optional[str], default: int = 0) -> int:
    """Safely converts string to int; handles '-', empty strings, or corrupt tokens."""
    if not value or value == "-":
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_log_line(line: str) -> Optional[dict]:
    """Parses a single access log line into structured fields with statusClass."""
    cleaned_line = line.strip()
    if not cleaned_line:
        return None

    match = LOG_PATTERN.match(cleaned_line)
    if not match:
        return None

    data = match.groupdict()

    # Safely split HTTP request tokens
    request_parts = data['request'].split()
    data['method'] = request_parts[0].upper() if len(request_parts) > 0 else ''
    data['endpoint'] = request_parts[1] if len(request_parts) > 1 else ''
    data['protocol'] = request_parts[2] if len(request_parts) > 2 else ''

    # Compute statusClass (e.g., 200 -> "2xx")
    status = data.get('status', '')
    data['statusClass'] = f"{status[0]}xx" if len(status) == 3 and status.isdigit() else "unknown"

    # Normalize missing byte size
    data['size'] = safe_int(data.get('size'), default=0)

    data['referer'] = "" if data.get('referer') == "-" else (data.get('referer') or "")
    data['user_agent'] = "" if data.get('user_agent') == "-" else (data.get('user_agent') or "")

    return data


def _normalize_filter_set(filter_arg: Optional[Union[str, Iterable[str]]]) -> Optional[Set[str]]:
    """Helper to convert a string or sequence of strings to a set of stripped strings."""
    if filter_arg is None:
        return None
    if isinstance(filter_arg, str):
        return {filter_arg.strip()}
    return {item.strip() for item in filter_arg}


def parse_access_logs_to_csv(
    log_source: Optional[Iterable[str]],
    output_csv_path: str,
    include_raw_request: bool = False,
    methods: Optional[Union[str, Iterable[str]]] = None,
    status_classes: Optional[Union[str, Iterable[str]]] = None,
) -> Dict[str, int]:
    """
    Parses access logs, applies filters, and writes results to CSV.
    Guarantees a valid CSV with headers even if log_source is empty or no lines match.
    """
    fieldnames = [
        'ip', 'ident', 'auth', 'timestamp',
        'method', 'endpoint', 'protocol',
        'status', 'statusClass', 'size',
        'referer', 'user_agent'
    ]
    if include_raw_request:
        fieldnames.append('request')

    # Normalize filters for case-insensitive exact matching
    raw_methods = _normalize_filter_set(methods)
    raw_classes = _normalize_filter_set(status_classes)

    target_methods = {m.upper() for m in raw_methods} if raw_methods else None
    target_classes = {sc.lower() for sc in raw_classes} if raw_classes else None

    written_count = 0
    malformed_count = 0
    filtered_count = 0

    # Ensure log_source is safely iterable even if passed None
    safe_log_source = log_source if log_source is not None else ()

    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        
        # Explicitly written first to guarantee valid CSV headers on empty or 0-match runs
        writer.writeheader()

        for line in safe_log_source:
            if not line.strip():
                continue

            parsed = parse_log_line(line)
            if parsed is None:
                malformed_count += 1
                continue

            # Method filter check
            if target_methods and parsed['method'] not in target_methods:
                filtered_count += 1
                continue

            # Status class filter check
            if target_classes and parsed['statusClass'].lower() not in target_classes:
                filtered_count += 1
                continue

            writer.writerow(parsed)
            written_count += 1

    return {
        "written": written_count,
        "skipped_malformed": malformed_count,
        "filtered_out": filtered_count,
        "total": written_count + malformed_count + filtered_count
    }