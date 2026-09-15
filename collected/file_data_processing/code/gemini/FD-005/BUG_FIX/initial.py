import csv
import io
import sys

# Define standard severity rankings (higher number = higher priority)
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
    """Sorts CSV log records by timestamp (asc), severity (desc), and sequence (asc).

    Preserves exact message text and outputs valid deterministic CSV.
    """
    reader = csv.reader(input_stream)

    try:
        header = next(reader)
    except StopIteration:
        return

    # Normalize header names for robust column index lookup
    header_lower = [col.strip().lower() for col in header]
    timestamp_idx = header_lower.index("timestamp")
    severity_idx = header_lower.index("severity")

    # Read rows and append zero-based sequence number
    indexed_rows = []
    for seq_num, row in enumerate(reader):
        if not row:
            continue
        indexed_rows.append((seq_num, row))

    def sort_key(item):
        seq_num, row = item
        timestamp = row[timestamp_idx].strip()
        raw_severity = row[severity_idx].strip().upper()

        # Unknown severities default to -1 to sort after defined severities
        severity_rank = SEVERITY_ORDER.get(raw_severity, -1)

        # Primary: Timestamp ascending
        # Secondary: Severity descending (-severity_rank reverses numeric sort)
        # Tertiary: Zero-based sequence number ascending
        return (timestamp, -severity_rank, seq_num)

    indexed_rows.sort(key=sort_key)

    # Write sorted data back to output stream with standard RFC 4180 CSV rules
    writer = csv.writer(
        output_stream, lineterminator="\n", quoting=csv.QUOTE_MINIMAL
    )
    writer.writerow(header)
    for _, row in indexed_rows:
        writer.writerow(row)


if __name__ == "__main__":
    # Example usage reading from standard input and writing to standard output
    sort_csv_logs(sys.stdin, sys.stdout)