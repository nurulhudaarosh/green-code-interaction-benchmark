import csv
import sys
from datetime import datetime

SEVERITY_ORDER = {
    "DEBUG": 0,
    "INFO": 1,
    "WARN": 2,
    "WARNING": 2,
    "ERROR": 3,
    "CRITICAL": 4,
    "FATAL": 5,
}


def parse_timestamp(ts):
    ts = ts.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return datetime.min


def severity_rank(sev):
    return SEVERITY_ORDER.get(sev.strip().upper(), -1)


def sort_csv(input_path, output_path):
    with open(input_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            pass
        return

    header = rows[0]
    data = rows[1:]

    header_lower = [h.strip().lower() for h in header]
    try:
        ts_idx = header_lower.index("timestamp")
    except ValueError:
        ts_idx = 0
    try:
        sev_idx = header_lower.index("severity")
    except ValueError:
        sev_idx = 1 if len(header) > 1 else 0

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
    if len(sys.argv) != 3:
        print("Usage: python csv_log_sorter.py <input.csv> <output.csv>")
        sys.exit(1)
    sort_csv(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()