import csv
import sys

# Severity priority mapping (higher value = higher priority / descending order)
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
    """Returns integer rank for severity string. Unknown severities get rank -1."""
    return SEVERITY_ORDER.get(str(severity_str).strip().upper(), -1)


def sort_csv_logs(
    input_file: str,
    output_file: str,
    timestamp_col: str = "timestamp",
    severity_col: str = "severity",
):
    """Reads a CSV log file, adds a zero-based sequence number to each record,

    sorts by:
      1. Timestamp (ascending)
      2. Severity (descending priority)
      3. Original Sequence Number (ascending, to maintain stability)

    Writes valid, deterministic CSV back out with quoted fields preserved.
    """
    with open(input_file, mode="r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []

        if "sequence" not in fieldnames:
            # Place sequence column right at the start
            fieldnames = ["sequence"] + fieldnames

        rows = []
        for idx, row in enumerate(reader):
            row["sequence"] = idx
            rows.append(row)

    # Sort key tuple:
    # 1. timestamp_col ascending
    # 2. -get_severity_weight(...) for severity descending
    # 3. original sequence ascending
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
            quoting=csv.QUOTE_MINIMAL,  # Properly quotes fields containing commas, quotes, or newlines
            lineterminator="\n",  # Ensures deterministic line endings across systems
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        sort_csv_logs(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python log_sorter.py <input_csv> <output_csv>")