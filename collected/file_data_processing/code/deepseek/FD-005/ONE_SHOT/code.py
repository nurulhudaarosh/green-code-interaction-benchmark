import csv
import sys
from datetime import datetime

SEVERITY_ORDER = {
    "DEBUG": 1,
    "INFO": 2,
    "WARNING": 3,
    "WARN": 3,
    "ERROR": 4,
    "CRITICAL": 5,
    "FATAL": 6,
}

TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y/%m/%d %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%Y-%m-%d",
]


def parse_timestamp(value):
    value = (value or "").strip()
    if not value:
        return datetime.min
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.min


def severity_rank(value):
    return SEVERITY_ORDER.get((value or "").strip().upper(), 0)


def sort_csv(input_path, output_path, timestamp_col="timestamp", severity_col="severity"):
    with open(input_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            pass
        return

    header = rows[0]
    data = rows[1:]

    try:
        ts_idx = header.index(timestamp_col)
    except ValueError:
        ts_idx = 0
    try:
        sev_idx = header.index(severity_col)
    except ValueError:
        sev_idx = 1

    indexed = []
    for seq, row in enumerate(data):
        ts = row[ts_idx] if ts_idx < len(row) else ""
        sev = row[sev_idx] if sev_idx < len(row) else ""
        indexed.append((parse_timestamp(ts), -severity_rank(sev), seq, row))

    indexed.sort(key=lambda x: (x[0], x[1], x[2]))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(header)
        for _, _, _, row in indexed:
            writer.writerow(row)


def main():
    if len(sys.argv) < 3:
        print("Usage: python csv_log_sorter.py <input.csv> <output.csv>")
        sys.exit(1)
    sort_csv(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()