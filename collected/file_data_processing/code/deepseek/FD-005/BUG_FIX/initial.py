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
        return (1, 0, "")
    formats = (
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    )
    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is not None:
                epoch = dt.timestamp()
            else:
                epoch = dt.replace(tzinfo=None).timestamp()
            return (0, epoch, value)
        except ValueError:
            continue
    return (1, 0, value)


def severity_rank(value):
    return SEVERITY_ORDER.get((value or "").strip().upper(), -1)


def sort_log(input_path, output_path):
    with open(input_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        open(output_path, "w", newline="", encoding="utf-8").close()
        return

    header = rows[0]
    data = rows[1:]

    lowered = [h.strip().lower() for h in header]

    def find_col(*names):
        for name in names:
            if name in lowered:
                return lowered.index(name)
        return None

    ts_col = find_col("timestamp", "time", "date", "datetime")
    sev_col = find_col("severity", "level", "loglevel", "priority")

    if ts_col is None:
        ts_col = 0
    if sev_col is None:
        sev_col = 1 if len(header) > 1 else 0

    decorated = []
    for seq, row in enumerate(data):
        ts_val = row[ts_col] if ts_col < len(row) else ""
        sev_val = row[sev_col] if sev_col < len(row) else ""
        ts_key = parse_timestamp(ts_val)
        sev_key = severity_rank(sev_val)
        decorated.append((ts_key, -sev_key, seq, row))

    decorated.sort(key=lambda item: (item[0], item[1], item[2]))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(header)
        for _, _, _, row in decorated:
            writer.writerow(row)


def main():
    if len(sys.argv) != 3:
        print("Usage: python log_sorter.py <input.csv> <output.csv>", file=sys.stderr)
        sys.exit(1)
    sort_log(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()