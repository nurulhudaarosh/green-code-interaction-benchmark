import csv
import sys
from datetime import datetime

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

def parse_timestamp(value):
    value = (value or "").strip()
    if not value:
        return datetime.min
    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%dT%H:%M:%S",
    )
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min

def severity_rank(value):
    return SEVERITY_ORDER.get((value or "").strip().upper(), -1)

def sort_logs(input_path, output_path, timestamp_col="timestamp", severity_col="severity"):
    with open(input_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("Input CSV is empty")

        try:
            ts_idx = header.index(timestamp_col)
        except ValueError:
            raise ValueError(f"Missing timestamp column: {timestamp_col}")
        try:
            sev_idx = header.index(severity_col)
        except ValueError:
            raise ValueError(f"Missing severity column: {severity_col}")

        indexed_rows = []
        for seq, row in enumerate(reader):
            if not row:
                continue
            ts_value = row[ts_idx] if ts_idx < len(row) else ""
            sev_value = row[sev_idx] if sev_idx < len(row) else ""
            indexed_rows.append((seq, row, ts_value, sev_value))

    indexed_rows.sort(
        key=lambda item: (
            parse_timestamp(item[2]),
            -severity_rank(item[3]),
            item[0],
        )
    )

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(header)
        for _, row, _, _ in indexed_rows:
            writer.writerow(row)

def main():
    if len(sys.argv) != 3:
        print("Usage: python log_sorter.py <input.csv> <output.csv>", file=sys.stderr)
        sys.exit(1)
    sort_logs(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
    main()