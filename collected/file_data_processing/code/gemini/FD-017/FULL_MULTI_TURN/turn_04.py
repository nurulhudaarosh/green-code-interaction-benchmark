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
    """Validates records, aggregates counts, pivots every observed event type into a column,

    fills absent combinations with zero, and guarantees deterministic column ordering
    (alphabetical) regardless of input arrival order.

    Malformed dates, invalid counts, and missing required keys are skipped without throwing exceptions.
    """
    if not isinstance(records, list) or not records:
        return pd.DataFrame()

    required_keys = {date_col, region_col, event_type_col, count_col}
    valid_records = []

    # 1. Validation and Record Extraction Loop
    for record in records:
        try:
            if not isinstance(record, dict):
                continue

            if not required_keys.issubset(record.keys()):
                continue

            date_val = record[date_col]
            region_val = record[region_col]
            event_type_val = record[event_type_col]
            count_val = record[count_col]

            if date_val is None or region_val is None or event_type_val is None:
                continue

            region_str = str(region_val).strip()
            event_type_str = str(event_type_val).strip()

            if not region_str or not event_type_str:
                continue

            # Safe date parsing
            try:
                parsed_date = pd.to_datetime(date_val, errors="raise").strftime("%Y-%m-%d")
            except (ValueError, TypeError, OverflowError):
                continue

            # Safe count parsing (filtering out booleans and non-numeric/negative values)
            try:
                if isinstance(count_val, bool):
                    continue

                count_num = float(count_val)
                if pd.isna(count_num) or count_num < 0:
                    continue

                count_num = int(count_num) if count_num.is_integer() else count_num
            except (ValueError, TypeError, OverflowError):
                continue

            valid_records.append(
                {
                    date_col: parsed_date,
                    region_col: region_str,
                    event_type_col: event_type_str,
                    count_col: count_num,
                }
            )
        except Exception:
            continue

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

    # 3. Pivot event types into columns
    pivoted_df = aggregated_df.pivot(
        index=[date_col, region_col],
        columns=event_type_col,
        values=count_col,
    )

    # 4. Fill absent combinations with 0 (fill_value)
    pivoted_df = pivoted_df.fillna(fill_value)

    if isinstance(fill_value, int):
        pivoted_df = pivoted_df.astype(int)

    # 5. Guarantee Deterministic Column & Index Ordering
    # Sort index levels (date, region)
    pivoted_df = pivoted_df.sort_index(level=[date_col, region_col])

    # Explicit lexicographical sort on column names regardless of arrival sequence
    deterministic_columns = sorted(list(pivoted_df.columns))
    pivoted_df = pivoted_df.reindex(columns=deterministic_columns)

    # Remove column axis label for clean output presentation
    pivoted_df.columns.name = None

    return pivoted_df


# Example Usage showing arbitrary arrival order resulting in deterministic output
if __name__ == "__main__":
    # Arrival Order 1: "signup", "view", "click"
    batch_1 = [
        {"date": "2026-03-15", "region": "North", "event_type": "signup", "count": 1},
        {"date": "2026-03-15", "region": "North", "event_type": "view", "count": 10},
        {"date": "2026-03-15", "region": "North", "event_type": "click", "count": 5},
    ]

    # Arrival Order 2: "click", "signup", "view"
    batch_2 = [
        {"date": "2026-03-15", "region": "North", "event_type": "click", "count": 5},
        {"date": "2026-03-15", "region": "North", "event_type": "signup", "count": 1},
        {"date": "2026-03-15", "region": "North", "event_type": "view", "count": 10},
    ]

    df1 = pivot_event_data(batch_1)
    df2 = pivot_event_data(batch_2)

    # Columns will always be sorted alphabetically: ['click', 'signup', 'view']
    print("Batch 1 Columns:", list(df1.columns))
    print("Batch 2 Columns:", list(df2.columns))
    print("\nDataFrames identical:", df1.equals(df2))