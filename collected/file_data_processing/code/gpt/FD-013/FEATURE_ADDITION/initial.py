import csv
import sys
import statistics


def main():
    if len(sys.argv) != 2:
        print("Usage: python statistics.py input.csv")
        return

    input_file = sys.argv[1]

    with open(input_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames

        if not columns:
            return

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

    print("column,count,min,max,mean,median")

    for column in columns:
        data = values[column]

        if not data:
            print(f"{column},0,,,,")
            continue

        print(
            f"{column},"
            f"{len(data)},"
            f"{min(data)},"
            f"{max(data)},"
            f"{statistics.mean(data)},"
            f"{statistics.median(data)}"
        )


if __name__ == "__main__":
    main()