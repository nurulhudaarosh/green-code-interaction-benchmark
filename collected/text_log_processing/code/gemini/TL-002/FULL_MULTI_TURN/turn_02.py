import csv
import re
from typing import Dict, Iterable, Optional

# Matches standard Common and Combined Log Formats
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
    """
    Parses a single access log line.
    Returns a dictionary of parsed fields, or None if the line is corrupt/unmatched.
    """
    cleaned_line = line.strip()
    if not cleaned_line:
        return None

    match = LOG_PATTERN.match(cleaned_line)
    if not match:
        return None

    data = match.groupdict()

    # Safely unpack HTTP request parts (handles malformed requests like "-" or "GARBAGE")
    request_parts = data['request'].split()
    data['method'] = request_parts[0] if len(request_parts) > 0 else ''
    data['endpoint'] = request_parts[1] if len(request_parts) > 1 else ''
    data['protocol'] = request_parts[2] if len(request_parts) > 2 else ''

    # Compute statusClass (e.g., 200 -> "2xx")
    status = data.get('status', '')
    data['statusClass'] = f"{status[0]}xx" if len(status) == 3 and status.isdigit() else "unknown"

    # Safely convert size (handles '-' and corrupt numeric values)
    data['size'] = safe_int(data.get('size'), default=0)

    # Clean up optional fields that might have matched as None or '-'
    data['referer'] = "" if data.get('referer') == "-" else (data.get('referer') or "")
    data['user_agent'] = "" if data.get('user_agent') == "-" else (data.get('user_agent') or "")

    return data


def parse_access_logs_to_csv(
    log_source: Iterable[str], 
    output_csv_path: str,
    include_raw_request: bool = False
) -> Dict[str, int]:
    """
    Reads lines from an iterable, writes valid rows to CSV, and counts skipped garbage lines.
    
    Returns:
        dict: {"written": int, "skipped": int, "total": int}
    """
    fieldnames = [
        'ip', 'ident', 'auth', 'timestamp',
        'method', 'endpoint', 'protocol',
        'status', 'statusClass', 'size',
        'referer', 'user_agent'
    ]
    if include_raw_request:
        fieldnames.append('request')

    written_count = 0
    skipped_count = 0

    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for line in log_source:
            # Skip empty whitespace-only lines without failing
            if not line.strip():
                continue

            parsed = parse_log_line(line)
            if parsed is not None:
                writer.writerow(parsed)
                written_count += 1
            else:
                skipped_count += 1

    return {
        "written": written_count,
        "skipped": skipped_count,
        "total": written_count + skipped_count
    }