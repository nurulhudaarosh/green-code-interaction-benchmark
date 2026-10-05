from collections import defaultdict
from datetime import datetime


def event_pivot(records, date_field="date", region_field="region", event_field="event"):
    """
    Validate records, aggregate counts by date/region, derive deterministic
    event-type columns, fill missing cells with zero, and sort rows.

    Malformed records (bad dates, missing/empty fields, non-dict entries)
    are skipped rather than raising, so processing always completes.
    """
    validated = []

    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            continue

        skip = False
        for field in (date_field, region_field, event_field):
            if field not in record:
                skip = True
                break
            value = record[field]
            if value is None or (isinstance(value, str) and not value.strip()):
                skip = True
                break
        if skip:
            continue

        raw_date = record[date_field]
        if isinstance(raw_date, datetime):
            date_value = raw_date.date().isoformat()
        elif isinstance(raw_date, str):
            try:
                date_value = datetime.strptime(raw_date.strip(), "%Y-%m-%d").date().isoformat()
            except ValueError:
                continue
        else:
            continue

        region_value = str(record[region_field]).strip()
        event_value = str(record[event_field]).strip()

        validated.append((date_value, region_value, event_value))

    if not validated:
        return {"columns": [], "rows": []}

    event_types = sorted({event for _, _, event in validated})

    counts = defaultdict(lambda: defaultdict(int))
    regions = set()
    dates = set()

    for date_value, region_value, event_value in validated:
        counts[(date_value, region_value)][event_value] += 1
        regions.add(region_value)
        dates.add(date_value)

    columns = ["date", "region"] + event_types
    rows = []

    for date_value in sorted(dates):
        for region_value in sorted(regions):
            bucket = counts.get((date_value, region_value), {})
            row = {
                "date": date_value,
                "region": region_value,
            }
            for event_type in event_types:
                row[event_type] = bucket.get(event_type, 0)
            rows.append(row)

    rows.sort(key=lambda r: (r["date"], r["region"]))

    return {"columns": columns, "rows": rows}


if __name__ == "__main__":
    sample = [
        {"date": "2024-01-02", "region": "NA", "event": "click"},
        {"date": "not-a-date", "region": "EU", "event": "view"},
        {"date": "2024-01-01", "region": "NA", "event": "click"},
        {"date": "2024-01-01", "region": "NA", "event": "click"},
        {"date": "2024-01-02", "region": "EU", "event": "view"},
        {"date": None, "region": "NA", "event": "view"},
        {"region": "NA", "event": "view"},
        "not a dict",
        {"date": "2024-01-01", "region": "NA", "event": "view"},
    ]
    result = event_pivot(sample)
    print(result["columns"])
    for row in result["rows"]:
        print(row)