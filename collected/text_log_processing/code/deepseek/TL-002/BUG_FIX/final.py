import re
import csv

# Anchored regex; the trailing $ (via \Z) prevents partial matches on
# corrupted lines that merely start out looking valid.
LOG_RE = re.compile(
    r'^(?P<ip>\S+)\s+'
    r'\S+\s+'
    r'\S+\s+'
    r'\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<method>\S+)\s+'
    r'(?P<url>\S+)\s+'
    r'[^"]*"\s+'
    r'(?P<status>\d{3})\s+'
    r'(?P<size>\S+)'
    r'\s*\Z'
)


def convert_access_log(in_path, out_path, methods, status_classes):
    """
    Parse an Apache-style access log into a filtered CSV.

    - size '-' is treated as 0
    - malformed lines are skipped and counted, never raising
    - returns {'written': int, 'skipped': int}
    """
    methods_set = set(methods)
    status_classes_set = set(status_classes)

    written = 0
    skipped = 0

    with open(in_path, 'r', encoding='utf-8', errors='replace') as fin, \
         open(out_path, 'w', newline='', encoding='utf-8') as fout:

        writer = csv.writer(fout)
        writer.writerow(
            ['ip', 'timestamp', 'method', 'url',
             'status', 'statusClass', 'size']
        )

        for line in fin:
            try:
                row = _parse_line(line)
            except Exception:
                # Any unexpected error on a single line is treated as
                # malformed so the loop keeps going.
                skipped += 1
                continue

            if row is None:
                skipped += 1
                continue

            ip, timestamp, method, url, status, size = row

            # Filtering (empty containers = allow all).
            if methods_set and method not in methods_set:
                continue

            status_class = status[0] + 'xx'
            if status_classes_set and status_class not in status_classes_set:
                continue

            writer.writerow(
                [ip, timestamp, method, url, status, status_class, size]
            )
            written += 1

    return {'written': written, 'skipped': skipped}


def _parse_line(line):
    """
    Return (ip, timestamp, method, url, status, size) or None if the
    line is malformed. Never raises for expected bad input.
    """
    if not line:
        return None

    line = line.rstrip('\r\n')
    if not line:
        return None

    m = LOG_RE.match(line)
    if not m:
        return None

    ip = m.group('ip')
    timestamp = m.group('timestamp')
    method = m.group('method')
    url = m.group('url')
    status = m.group('status')
    size_raw = m.group('size')

    # size: '-' -> 0, otherwise must parse as an int.
    if size_raw == '-' or size_raw == '':
        size = 0
    else:
        try:
            size = int(size_raw)
        except (TypeError, ValueError):
            return None

    return ip, timestamp, method, url, status, size