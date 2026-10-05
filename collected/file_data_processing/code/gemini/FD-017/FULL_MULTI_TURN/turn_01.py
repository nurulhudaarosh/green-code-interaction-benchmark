from datetime import datetime
from typing import Any, Dict, List, Union
import pandas as pd


def pivot_event_data(
    records: List[Dict[str, Any]],
    date_col: str = "date",
    region_col: str = "region",
    event_type_col: str = "event_type",
    count_col: str = "count",
    fill_value: Union[int, float] = 0,
) -> pd.DataFrame:
    """Validates records, aggregates event counts by date and region, pivots event types into

    deterministic columns, fills missing values, and sorts the output.

    Parameters:
    -----------
    records : List[Dict[str, Any]]
        List of dictionaries containing raw event data.
    date_col : str, optional
        Key/Column name for dates (default 'date').
    region_col : str, optional
        Key/Column name for regions (default 'region').
    event_type_col : str, optional
        Key/Column name for event types (default 'event_type').
    count_col : str, optional
        Key/Column name for counts (default 'count').
    fill_value : Union[int, float], optional
        Value to fill missing cells with after pivot (default 0).

    Returns:
    --------
    pd.DataFrame
        Pivoted DataFrame indexed by [date, region] with sorted, deterministic
        event-type columns and fill_value for missing combinations.
    """
    if not records:
        return pd.DataFrame()

    required_keys = {date_col, region_col, event_type_col, count_col}
    valid_records = []

    # 1. Record Validation & Cleaning
    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            continue

        # Check required fields
        if not required_keys.issubset(record.keys()):
            continue

        date_val = record[date_col]
        region_val = record[region_col]
        event_type_val = record[event_type_col]
        count_val = record[count_col]

        # Validate non-null/non-empty string fields
        if not date_val or not region_val or not event_type_val:
            continue

        # Validate and standardise date format (YYYY-MM-DD or standard datetime string)
        try:
            parsed_date = pd.to_datetime(date_val).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue

        # Validate count is numeric and non-negative
        try:
            count_num = float(count_val)
            if count_num < 0:
                continue
            # Store as integer if whole number
            count_num = int(count_num) if count_num.is_integer() else count_num
        except (ValueError, TypeError):
            continue

        valid_records.append(
            {
                date_col: parsed_date,
                region_col: str(region_val).strip(),
                event_type_col: str(event_type_val).strip(),
                count_col: count_num,
            }
        )

    if not valid_records:
        return pd.DataFrame()

    df = pd.DataFrame(valid_records)

    # 2. Pre-aggregation by Date, Region, and Event Type
    aggregated_df = (
        df.groupby([date_col, region_col, event_type_col], as_index=False)[
            count_col
        ]
        .sum()
    )

    # 3. Pivot table creation with deterministic column ordering
    pivoted_df = aggregated_df.pivot(
        index=[date_col, region_col],
        columns=event_type_col,
        values=count_col,
    )

    # 4. Fill missing cells with fill_value and sort index/columns deterministically
    pivoted_df = pivoted_df.fillna(fill_value)

    # Ensure integer counts if fill_value is int and all values are integers
    if isinstance(fill_value, int):
        pivoted_df = pivoted_df.astype(int)

    # Deterministic sorting on index levels and column names
    pivoted_df = pivoted_df.sort_index(level=[date_col, region_col])
    sorted_columns = sorted(pivoted_df.columns.tolist())
    pivoted_df = pivoted_df[sorted_columns]

    # Reset name of columns axis for cleanliness
    pivoted_df.columns.name = None

    return pivoted_df


# Example Usage
if __name__ == "__main__":
    sample_records = [
        {"date": "2026-03-15", "region": "North", "event_type": "click", "count": 10},
        {"date": "2026-03-15", "region": "North", "event_type": "click", "count": 5},
        {"date": "2026-03-15", "region": "North", "event_type": "purchase", "count": 2},
        {"date": "2026-03-15", "region": "South", "event_type": "view", "count": 20},
        {"date": "2026-03-16", "region": "North", "event_type": "view", "count": 15},
        # Invalid records (skipped automatically):
        {"date": None, "region": "East", "event_type": "click", "count": 1},
        {"date": "2026-03-15", "region": "West", "event_type": "click", "count": -5},
        {"invalid_field": True},
    ]

    result = pivot_event_data(sample_records)
    print(result)