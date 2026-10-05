from datetime import datetime
from typing import Any, Dict, List, Tuple
import pandas as pd


def pivot_event_records(
    records: List[Dict[str, Any]],
    date_key: str = "date",
    region_key: str = "region",
    event_type_key: str = "event_type",
    sort_ascending: bool = True,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Validates records, aggregates counts by date, region, and event_type,

    pivots ALL observed event types into columns filled with zeros, and sorts by
    date and region.

    Returns:
        tuple: (pivoted_dataframe, invalid_records)
    """
    valid_records = []
    invalid_records = []

    # 1. Validation phase
    for record in records:
        if not isinstance(record, dict):
            invalid_records.append({"record": record, "reason": "Not a dictionary"})
            continue

        raw_date = record.get(date_key)
        raw_region = record.get(region_key)
        raw_event_type = record.get(event_type_key)

        if raw_date is None or raw_region is None or raw_event_type is None:
            invalid_records.append(
                {"record": record, "reason": "Missing required keys"}
            )
            continue

        # Validate and parse date
        if isinstance(raw_date, datetime):
            parsed_date = raw_date.strftime("%Y-%m-%d")
        else:
            try:
                parsed_date = pd.to_datetime(raw_date).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                invalid_records.append(
                    {"record": record, "reason": f"Invalid date: {raw_date}"}
                )
                continue

        valid_records.append(
            {
                "date": parsed_date,
                "region": str(raw_region).strip(),
                "event_type": str(raw_event_type).strip(),
            }
        )

    # Return empty DataFrame if no valid records exist
    if not valid_records:
        return pd.DataFrame(columns=["date", "region"]), invalid_records

    df = pd.DataFrame(valid_records)

    # 2. Derive deterministic set of all observed event-type columns
    all_observed_events = sorted(df["event_type"].unique().tolist())

    # 3. Aggregate counts by date, region, and event_type
    aggregated = (
        df.groupby(["date", "region", "event_type"]).size().reset_index(name="count")
    )

    # 4. Pivot every observed event type into a column & fill absent combinations with 0
    pivoted = aggregated.pivot_table(
        index=["date", "region"],
        columns="event_type",
        values="count",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    # Reindex columns to guarantee deterministic column order across all observed event types
    pivoted = pivoted.reindex(
        columns=["date", "region"] + all_observed_events, fill_value=0
    )

    # Clean up column index metadata
    pivoted.columns.name = None

    # 5. Sort rows deterministically by date and region
    pivoted = pivoted.sort_values(
        by=["date", "region"], ascending=sort_ascending
    ).reset_index(drop=True)

    return pivoted, invalid_records


# Example Usage:
if __name__ == "__main__":
    raw_data = [
        {"date": "2026-10-01", "region": "US-East", "event_type": "click"},
        {"date": "2026-10-01", "region": "US-East", "event_type": "click"},
        {"date": "2026-10-01", "region": "US-East", "event_type": "purchase"},
        {"date": "2026-10-01", "region": "EU-West", "event_type": "click"},
        {"date": "2026-10-02", "region": "US-East", "event_type": "signup"},
        {"date": "invalid-date", "region": "US-East", "event_type": "click"},  # Invalid
        {"date": "2026-10-01", "region": None, "event_type": "click"},  # Invalid
    ]

    df_result, bad_records = pivot_event_records(raw_data)

    print("--- Pivoted & Sorted DataFrame (Observed Events) ---")
    print(df_result)

    print("\n--- Invalid Records Log ---")
    print(bad_records)