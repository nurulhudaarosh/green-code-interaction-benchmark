import csv
import re
from typing import Iterable, Optional

# Matches standard Common and Combined Log Formats:
# IP ident auth [datetime] "METHOD path PROTOCOL" status size "referer" "user-agent"
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


def parse_log_line(line: str) -> Optional[dict]:
    """Parse a single access log line into structured fields with statusClass."""
    match = LOG_PATTERN.match(line.strip())
    if not match:
        return None

    data = match.groupdict()

    # Split the HTTP request component (METHOD, PATH, PROTOCOL)
    request_parts = data['request'].split()
    data['method'] = request_parts[0] if len(request_parts) > 0 else ''
    data['endpoint'] = request_parts[1] if len(request_parts) > 1 else ''
    data['protocol'] = request_parts[2] if len(request_parts) > 2 else ''

    # Derive statusClass (e.g., "200" -> "2xx")
    status = data['status']
    data['statusClass'] = f'{status[0]}xx' if status.isdigit() and len(status) == 3 else 'unknown'

    # Normalize missing byte size ('-' in logs)
    data['size'] = 0 if data['size'] == '-' else int(data['size'])

    return data


def parse_access_logs_to_csv(
    log_source: Iterable[str],
    output_csv_path: str,
    include_raw_request: bool = False,
) -> int:
    """Parses log lines from an iterable (file, list, generator) and writes them to a CSV file.

    Returns the number of successfully parsed and written records.
    """
    fieldnames = [
        'ip',
        'ident',
        'auth',
        'timestamp',
        'method',
        'endpoint',
        'protocol',
        'status',
        'statusClass',
        'size',
        'referer',
        'user_agent',
    ]

    if include_raw_request:
        fieldnames.append('request')

    parsed_count = 0

    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for line in log_source:
            parsed = parse_log_line(line)
            if parsed:
                writer.writerow(parsed)
                parsed_count += 1

    return parsed_count