import csv
import sys

def sort_log(input_path, output_path):
    with open(input_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Assign zero-based sequence numbers
    for i, row in enumerate(rows):
        row['_seq'] = i

    severity_order = {
        'CRITICAL': 5,
        'ERROR': 4,
        'WARNING': 3,
        'INFO': 2,
        'DEBUG': 1,
    }

    def sort_key(row):
        timestamp = row.get('timestamp', '')
        severity = severity_order.get(row.get('severity', '').upper(), 0)
        return (timestamp, -severity, row['_seq'])

    rows.sort(key=sort_key)

    for row in rows:
        del row['_seq']

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_MINIMAL,
            lineterminator='\n'
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python log_sorter.py <input.csv> <output.csv>")
        sys.exit(1)

    sort_log(sys.argv[1], sys.argv[2])