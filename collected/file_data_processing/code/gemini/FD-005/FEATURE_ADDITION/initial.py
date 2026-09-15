import csv
import io
import sys


def sort_csv_log(input_stream, output_stream):
    # Map severity levels to numeric priority for descending sort
    severity_order = {"CRITICAL": 5, "FATAL": 5, "ERROR": 4, "WARN": 3, "WARNING": 3, "INFO": 2, "DEBUG": 1, "TRACE": 0}

    reader = csv.reader(input_stream)
    try:
        header = next(reader)
    except StopIteration:
        return

    rows = []
    for seq, row in enumerate(reader):
        if not row:
            continue

        timestamp = row[0] if len(row) > 0 else ""
        severity_str = row[1].upper() if len(row) > 1 else ""
        severity_val = severity_order.get(severity_str, -1)

        # Sort key: timestamp ascending, severity descending, sequence ascending
        sort_key = (timestamp, -severity_val, seq)
        rows.append((sort_key, row))

    rows.sort(key=lambda x: x[0])

    writer = csv.writer(
        output_stream,
        dialect="unix",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    writer.writerow(header)
    for _, row in rows:
        writer.writerow(row)


if __name__ == "__main__":
    sort_csv_log(sys.stdin, sys.stdout)