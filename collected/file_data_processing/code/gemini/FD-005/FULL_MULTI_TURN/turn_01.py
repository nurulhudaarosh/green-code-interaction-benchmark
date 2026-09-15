import csv
import io
import sys

# Priority map for ordering severity descending
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


def sort_csv_logs(
    input_file,
    output_file,
    timestamp_col="timestamp",
    severity_col="severity",
):
    """Reads a CSV log file, assigns a 0-based sequence number to each row,

    sorts deterministically by:
      1. Timestamp (Ascending)
      2. Severity (Descending)
      3. Sequence number (Ascending)

    Preserves full message content including quoted commas, newlines, and quotes.
    """
    reader = csv.DictReader(input_file)
    fieldnames = reader.fieldnames if reader.fieldnames else []

    # Include sequence in output fieldnames if not present
    output_fieldnames = list(fieldnames)
    if "sequence" not in output_fieldnames:
        output_fieldnames.append("sequence")

    rows = []
    for seq, row in enumerate(reader):
        row["sequence"] = seq

        # Determine severity priority rank (default to -1 for unknown severities)
        sev_str = str(row.get(severity_col, "")).strip().upper()
        sev_rank = SEVERITY_ORDER.get(sev_str, -1)

        # Append tuple for sorting: (timestamp ASC, severity DESC, sequence ASC, row)
        rows.append(
            (row.get(timestamp_col, ""), -sev_rank, seq, row)
        )

    # Sort deterministically
    rows.sort(key=lambda x: (x[0], x[1], x[2]))

    writer = csv.DictWriter(
        output_file, fieldnames=output_fieldnames, lineterminator="\n"
    )
    writer.writeheader()
    for _, _, _, row in rows:
        writer.writerow(row)


# Example usage
if __name__ == "__main__":
    sample_csv = """timestamp,severity,message
2026-09-12T10:00:00,INFO,"System started, all services running"
2026-09-12T10:00:00,ERROR,"Database connection failed, retrying..."
2026-09-12T09:30:00,DEBUG,"Cache miss for key: user_123"
2026-09-12T10:00:00,ERROR,"Failed to bind to port 8080"
"""

    input_stream = io.StringIO(sample_csv.strip())
    output_stream = io.StringIO()

    sort_csv_logs(input_stream, output_stream)

    print(output_stream.getvalue())