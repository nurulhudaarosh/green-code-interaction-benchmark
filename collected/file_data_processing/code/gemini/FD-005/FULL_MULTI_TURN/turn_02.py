import csv
import io
import sys

# Severity hierarchy map for descending sort
SEVERITY_ORDER = {
    "CRITICAL": 6,
    "FATAL": 6,
    "ERROR": 5,
    "WARN": 4,
    "WARNING": 4,
    "INFO": 3,
    "DEBUG": 2,
    "TRACE": 1,
}


def sort_csv_logs(
    input_source,
    output_destination,
    timestamp_col="timestamp",
    severity_col="severity",
):
    """Sorts CSV logs using standard python `csv` module which correctly handles

    embedded commas, quotes, and multi-line strings within fields.

    Sorting hierarchy:
      1. Timestamp (Ascending)
      2. Severity (Descending)
      3. Original sequence number (Ascending - preserves original relative order)
    """
    # Force csv module to parse standard RFC 4180 CSVs strictly,
    # honoring quoted commas and escaped internal quotes correctly.
    reader = csv.DictReader(input_source, dialect="excel")
    fieldnames = reader.fieldnames if reader.fieldnames else []

    output_fieldnames = list(fieldnames)
    if "sequence" not in output_fieldnames:
        output_fieldnames.append("sequence")

    indexed_rows = []
    for seq_num, row in enumerate(reader):
        row["sequence"] = seq_num

        # Severity priority (higher number = higher priority)
        sev_name = str(row.get(severity_col, "")).strip().upper()
        sev_priority = SEVERITY_ORDER.get(sev_name, 0)

        # Sort Key: (timestamp ASC, -severity DESC, original sequence ASC)
        sort_key = (
            str(row.get(timestamp_col, "")),
            -sev_priority,
            seq_num,
        )

        indexed_rows.append((sort_key, row))

    # Sort deterministically
    indexed_rows.sort(key=lambda x: x[0])

    # csv.writer / csv.DictWriter correctly escapes fields containing commas or quotes
    writer = csv.DictWriter(
        output_destination,
        fieldnames=output_fieldnames,
        dialect="excel",
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )

    writer.writeheader()
    for _, row in indexed_rows:
        writer.writerow(row)


# Self-test demonstrating robust comma, newline, and quote preservation
if __name__ == "__main__":
    sample_data = (
        'timestamp,severity,message\n'
        '2026-09-12T10:00:00,INFO,"Normal log, no issue"\n'
        '2026-09-12T10:00:00,ERROR,"Failed to parse line 10, column 5, error: ""Syntax Failure"""\n'
        '2026-09-12T08:00:00,WARNING,"Multi-line message:\nLine 1, sub-part A\nLine 2, sub-part B"\n'
        '2026-09-12T10:00:00,ERROR,"Second error at same timestamp, keeping sequence order"\n'
    )

    input_buf = io.StringIO(sample_data)
    output_buf = io.StringIO()

    sort_csv_logs(input_buf, output_buf)
    print(output_buf.getvalue())