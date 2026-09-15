import csv
import io
import sys

# Priority mapping for severity ordering (higher value = higher priority)
SEVERITY_ORDER = {
    "CRITICAL": 5,
    "FATAL": 5,
    "ERROR": 4,
    "WARN": 3,
    "WARNING": 3,
    "INFO": 2,
    "DEBUG": 1,
    "TRACE": 0,
}


def sort_csv_logs(input_stream, output_stream):
    """Reads CSV log data from input_stream, sorts by:

    1. Timestamp (ascending)
    2. Severity (descending priority)
    3. Original sequence number (ascending)

    and writes the output as a valid CSV to output_stream.
    """
    reader = csv.reader(input_stream)

    try:
        header = next(reader)
    except StopIteration:
        return

    # Normalize header column names to lowercase for robust indexing
    header_lower = [col.strip().lower() for col in header]

    try:
        timestamp_idx = header_lower.index("timestamp")
        severity_idx = header_lower.index("severity")
    except ValueError as e:
        raise ValueError("CSV missing required header column: 'timestamp' or 'severity'") from e

    indexed_rows = []
    for seq, row in enumerate(reader):
        if not row:
            continue
        timestamp = row[timestamp_idx].strip()
        severity_raw = row[severity_idx].strip().upper()
        # Fall back to -1 if severity string is unknown
        severity_priority = SEVERITY_ORDER.get(severity_raw, -1)

        # Primary key: Timestamp (ASC)
        # Secondary key: Severity priority inverted (DESC -> lower is higher priority)
        # Tertiary key: Sequence number (ASC)
        indexed_rows.append((timestamp, -severity_priority, seq, row))

    indexed_rows.sort(key=lambda x: (x[0], x[1], x[2]))

    writer = csv.writer(
        output_stream,
        dialect="unix",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n"
    )

    writer.writerow(header)
    for _, _, _, row in indexed_rows:
        writer.writerow(row)


if __name__ == "__main__":
    # Example usage reading from standard input and writing to standard output
    sort_csv_logs(sys.stdin, sys.stdout)