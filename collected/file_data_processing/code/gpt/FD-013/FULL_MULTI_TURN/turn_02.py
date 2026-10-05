import csv
import sys
import statistics


def main():
    input_file = sys.argv[1]

    with open(input_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames
        values = {column: [] for column in columns}

        for row in reader:
            for column in columns:
                value = row.get(column, "").strip()

                if value == "":
                    continue

                try:
                    values[column].append(float(value))
                except ValueError:
                    continue

    for column in columns:
        data = values[column]

        if not data:
            print(f"{column}: count=0, minimum=N/A, maximum=N/A, mean=N/A, median=N/A")
        else:
            print(
                f"{column}: "
                f"count={len(data)}, "
                f"minimum={min(data)}, "
                f"maximum={max(data)}, "
                f"mean={statistics.mean(data)}, "
                f"median={statistics.median(data)}"
            )


if __name__ == "__main__":
    main()