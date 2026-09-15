import csv
import sys

def sort_log(input_path, output_path):
    with open(input_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, quotechar='"', delimiter=',', skipinitialspace=False)
        rows = list(reader)

    header, data_rows = rows[0], rows[1:]

    ts_idx = header.index('timestamp')
    sev_idx = header.index('severity')

    severity_order = {
        'CRITICAL': 5,
        'ERROR': 4,
        'WARNING': 3,
        'INFO': 2,
        'DEBUG': 1,
    }

    # Assign zero-based sequence number as parsed, preserving original file order
    indexed_rows = [(i, row) for i, row in enumerate(data_rows)]

    def sort_key(item):
        seq, row = item
        timestamp = row[ts_idx]
        severity = severity_order.get(row[sev_idx].strip().upper(), 0)
        # seq is the final tiebreaker -> guarantees a stable, deterministic order
        # even when many rows share timestamp and severity
        return (timestamp, -severity, seq)

    indexed_rows.sort(key=sort_key)

    output_header = header + ['sequence']

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(
            f,
            quotechar='"',
            delimiter=',',
            quoting=csv.QUOTE_MINIMAL,
            lineterminator='\n'
        )
        writer.writerow(output_header)
        for seq, row in indexed_rows:
            writer.writerow(row + [seq])


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python log_sorter.py <input.csv> <output.csv>")
        sys.exit(1)

    sort_log(sys.argv[1], sys.argv[2])