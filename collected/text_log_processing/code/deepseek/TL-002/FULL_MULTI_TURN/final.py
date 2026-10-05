import csv
import re
from typing import List, Dict, Optional, Iterable, Set
from datetime import datetime

VALID_STATUS_CLASSES = ('1xx', '2xx', '3xx', '4xx', '5xx')

FIELDNAMES = [
    'ip', 'user', 'timestamp', 'method', 'path', 'protocol',
    'status_code', 'status_class', 'size', 'referer', 'user_agent'
]


def parse_access_log_to_csv(
    log_lines: List[str],
    output_file: str,
    methods: Optional[Iterable[str]] = None,
    status_classes: Optional[Iterable[str]] = None,
) -> Dict[str, int]:
    """
    Parse access log lines and write them to a CSV file with status class.

    Always produces a valid CSV with a header row, even if no entries match.

    Args:
        log_lines: List of access log lines (Common Log Format or Combined Log Format).
        output_file: Path to the output CSV file.
        methods: Optional iterable of HTTP methods to keep (case-insensitive).
        status_classes: Optional iterable of status classes to keep.

    Returns:
        {'written': N, 'skipped': M, 'filtered': K}
    """
    method_filter: Optional[Set[str]] = None
    if methods is not None:
        method_filter = {m.upper() for m in methods}

    status_filter: Optional[Set[str]] = None
    if status_classes is not None:
        status_filter = {s.lower() for s in status_classes}
        invalid = status_filter - set(VALID_STATUS_CLASSES)
        if invalid:
            raise ValueError(
                f"Invalid status class(es): {sorted(invalid)}. "
                f"Valid values: {list(VALID_STATUS_CLASSES)}"
            )

    log_pattern = re.compile(
        r'^(?P<ip>\S+) '
        r'\S+ '
        r'(?P<user>\S+) '
        r'\[(?P<timestamp>[^\]]+)\] '
        r'"(?P<method>\S+) '
        r'(?P<path>\S+) '
        r'(?P<protocol>[^"]*)" '
        r'(?P<status>\d{3}) '
        r'(?P<size>\S+)'
        r'(?:\s+"(?P<referer>[^"]*)" '
        r'"(?P<user_agent>[^"]*)")?'
    )

    def get_status_class(status_code: int) -> str:
        if 100 <= status_code < 200:
            return '1xx'
        if 200 <= status_code < 300:
            return '2xx'
        if 300 <= status_code < 400:
            return '3xx'
        if 400 <= status_code < 500:
            return '4xx'
        if 500 <= status_code < 600:
            return '5xx'
        return 'unknown'

    def parse_timestamp(timestamp_str: str) -> str:
        try:
            dt = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
            return dt.isoformat()
        except (ValueError, TypeError):
            return timestamp_str

    def parse_size(size_str: str) -> int:
        if not size_str or size_str == '-':
            return 0
        try:
            return int(size_str)
        except ValueError:
            return 0

    parsed_entries = []
    skipped = 0
    filtered = 0

    for line_num, line in enumerate(log_lines, start=1):
        line = line.strip()

        if not line:
            continue

        match = log_pattern.match(line)
        if not match:
            skipped += 1
            print(f"Warning: Skipping unparseable line {line_num}: {line[:100]}")
            continue

        data = match.groupdict()

        try:
            status_code = int(data['status'])
        except (ValueError, TypeError):
            skipped += 1
            print(f"Warning: Skipping line {line_num} (bad status): {line[:100]}")
            continue

        method = data['method']
        status_class = get_status_class(status_code)

        if method_filter is not None and method.upper() not in method_filter:
            filtered += 1
            continue
        if status_filter is not None and status_class not in status_filter:
            filtered += 1
            continue

        entry = {
            'ip': data['ip'],
            'user': data['user'],
            'timestamp': parse_timestamp(data['timestamp']),
            'method': method,
            'path': data['path'],
            'protocol': (data['protocol'] or '').strip(),
            'status_code': status_code,
            'status_class': status_class,
            'size': parse_size(data['size']),
            'referer': data.get('referer') or '',
            'user_agent': data.get('user_agent') or '',
        }
        parsed_entries.append(entry)

    # Always write the header, even when parsed_entries is empty.
    # DictWriter.writeheader() emits the header row; writerows([]) is a no-op.
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        if parsed_entries:
            writer.writerows(parsed_entries)

    stats = {
        'written': len(parsed_entries),
        'skipped': skipped,
        'filtered': filtered,
    }
    print(
        f"Wrote {stats['written']} entries to {output_file} "
        f"({stats['skipped']} skipped, {stats['filtered']} filtered)"
    )
    return stats


def parse_log_file_to_csv(
    input_file: str,
    output_file: str,
    methods: Optional[Iterable[str]] = None,
    status_classes: Optional[Iterable[str]] = None,
) -> Dict[str, int]:
    """Parse an access log file and write to CSV, with optional filters."""
    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        log_lines = f.readlines()

    return parse_access_log_to_csv(
        log_lines, output_file, methods=methods, status_classes=status_classes
    )


def get_status_class_summary(csv_file: str) -> Dict[str, int]:
    """Get a summary of status classes from the CSV file."""
    summary: Dict[str, int] = {}
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sc = row['status_class']
            summary[sc] = summary.get(sc, 0) + 1
    return summary


if __name__ == "__main__":
    sample_logs = [
        '192.168.1.1 - - [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.0" 200 2326 "-" "Mozilla/5.0"',
        '192.168.1.2 - admin [10/Oct/2000:13:56:36 -0700] "POST /api/login HTTP/1.1" 401 128 "-" "curl/7.64.1"',
        '10.0.0.3 - - [10/Oct/2000:14:00:36 -0700] "GET /error HTTP/1.1" 500 1024 "-" "Mozilla/5.0"',
    ]

    print("=== Empty log lines list ===")
    parse_access_log_to_csv([], 'empty.csv')

    print("\n=== Log with only garbage ===")
    parse_access_log_to_csv(['garbage', 'more garbage'], 'garbage.csv')

    print("\n=== Zero-match filter (DELETE) ===")
    parse_access_log_to_csv(sample_logs, 'no_delete.csv', methods=['DELETE'])

    print("\n=== Zero-match status filter (1xx) ===")
    parse_access_log_to_csv(sample_logs, 'no_1xx.csv', status_classes=['1xx'])

    # Verify each output has exactly the header row
    print("\n=== Verification ===")
    for fname in ['empty.csv', 'garbage.csv', 'no_delete.csv', 'no_1xx.csv']:
        with open(fname, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        assert len(lines) == 1, f"{fname} should have exactly 1 line, got {len(lines)}"
        assert lines[0].strip() == ','.join(FIELDNAMES), f"{fname} header mismatch"
        print(f"  {fname}: OK (header only, {len(lines)} line)")

    # And confirm a populated run still round-trips
    print("\n=== Populated run ===")
    parse_access_log_to_csv(sample_logs, 'populated.csv')
    print(f"  Summary: {get_status_class_summary('populated.csv')}")