import csv
import io
import sys

# Standard log severity precedence (higher number = higher priority)
SEVERITY_ORDER = {
    "FATAL": 6,
    "CRITICAL": 5,
    "ERROR": 4,
    "WARNING": 3,
    "WARN": 3,
    "INFO": 2,
    "DEBUG": 1,
    "TRACE": 0,
}


def sort_csv_logs(input_stream, output_stream):
    """Sorts CSV log records by timestamp ascending, severity descending, then sequence ascending.

    Uses Python's native csv module to correctly handle quotes, embedded commas,
    and multiline messages according to RFC 4180.
    """
    # csv.reader transparently handles embedded commas and escaped quotes within fields
    reader = csv.reader(input_stream)

    try:
        header = next(reader)
    except StopIteration:
        return  # Handle empty file gracefully

    header_lower = [col.strip().lower() for col in header]

    try:
        timestamp_idx = header_lower.index("timestamp")
        severity_idx = header_lower.index("severity")
    except ValueError as e:
        raise ValueError(
            "CSV input must contain 'timestamp' and 'severity' headers."
        ) from e

    # Assign zero-based original sequence number to maintain stability
    indexed_rows = []
    for seq_num, row in enumerate(reader):
        if not row:
            continue
        indexed_rows.append((seq_num, row))

    def sort_key(item):
        seq_num, row = item
        timestamp = row[timestamp_idx].strip()
        raw_severity = row[severity_idx].strip().upper()

        # Unknown severity levels get lowest precedence (-1)
        severity_rank = SEVERITY_ORDER.get(raw_severity, -1)

        # 1. Timestamp ascending
        # 2. Severity descending (inverted numerical rank)
        # 3. Original 0-based sequence number ascending
        return (timestamp, -severity_rank, seq_num)

    indexed_rows.sort(key=sort_key)

    # csv.writer guarantees proper quoting for fields containing commas or quotes
    writer = csv.writer(
        output_stream,
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writerow(header)
    for _, row in indexed_rows:
        writer.writerow(row)


if __name__ == "__main__":
    sort_csv_logs(sys.stdin, sys.stdout)