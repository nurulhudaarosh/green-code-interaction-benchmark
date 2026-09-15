import csv
import sys

SEVERITY_ORDER = {
    "CRITICAL": 5,
    "FATAL": 5,
    "ERROR": 4,
    "WARNING": 3,
    "WARN": 3,
    "INFO": 2,
    "DEBUG": 1,
    "TRACE": 0,
}


def get_severity_weight(severity_str: str) -> int:
    return SEVERITY_ORDER.get(str(severity_str).strip().upper(), -1)


def sort_csv_logs(
    input_file: str,
    output_file: str,
    timestamp_col: str = "timestamp",
    severity_col: str = "severity",
):
    with open(input_file, mode="r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []

        if "sequence" not in fieldnames:
            fieldnames = ["sequence"] + fieldnames

        rows = []
        for seq, row in enumerate(reader):
            row["sequence"] = seq
            rows.append(row)

    # Deterministic sort order:
    # 1. Timestamp ascending
    # 2. Severity weight descending (-get_severity_weight)
    # 3. Original sequence number ascending (ensures stable tie-breaking)
    rows.sort(
        key=lambda r: (
            r.get(timestamp_col, ""),
            -get_severity_weight(r.get(severity_col, "")),
            r["sequence"],
        )
    )

    with open(output_file, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_MINIMAL,
            doublequote=True,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        sort_csv_logs(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python log_sorter.py <input_csv> <output_csv>")