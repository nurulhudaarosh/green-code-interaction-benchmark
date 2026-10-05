import pandas as pd


def process_sensor_timeseries(
    df: pd.DataFrame,
    sensor_col: str = "sensor_id",
    time_col: str = "timestamp",
    value_col: str = "value",
    inserted_col: str = "is_interpolated",
) -> pd.DataFrame:
    """Sorts time-series readings per sensor, fills missing interior hourly timestamps

    via linear interpolation (handling consecutive gaps without extrapolating outside
    the observed boundary range), marks inserted rows, and returns a deterministic DataFrame.
    """
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])

    processed_groups = []

    for sensor_id, group in df.groupby(sensor_col):
        # Sort and deduplicate timestamps per sensor
        group = group.sort_values(time_col).drop_duplicates(subset=[time_col])
        group = group.set_index(time_col)

        # Flag original rows
        group[inserted_col] = False

        # Resample strictly between min and max observation timestamps (no exterior extrapolation)
        resampled = group.resample("1h").asfreq()

        # Mark newly inserted rows
        resampled[inserted_col] = resampled[inserted_col].fillna(True)

        # Restore sensor_id column for interpolated rows
        resampled[sensor_col] = sensor_id

        # Linear interpolation naturally handles single and consecutive interior gaps
        # limit_area='inside' explicitly prevents extrapolating beyond first/last non-null value
        resampled[value_col] = resampled[value_col].interpolate(
            method="linear", limit_area="inside"
        )

        processed_groups.append(resampled.reset_index())

    # Combine all sensor groups
    result = pd.concat(processed_groups, ignore_index=True)

    # Sort deterministically by sensor_id and timestamp
    result = result.sort_values(
        by=[sensor_col, time_col], ascending=[True, True]
    ).reset_index(drop=True)

    # Ensure consistent column ordering
    columns_order = [sensor_col, time_col, value_col, inserted_col]
    extra_cols = [c for c in result.columns if c not in columns_order]

    return result[columns_order + extra_cols]


if __name__ == "__main__":
    # Example Usage demonstrating consecutive missing hours handling
    raw_data = pd.DataFrame(
        {
            "sensor_id": ["A", "A", "B", "B"],
            "timestamp": [
                "2026-03-30 08:00:00",
                "2026-03-30 11:00:00",  # 2 consecutive missing hours (09:00, 10:00)
                "2026-03-30 01:00:00",
                "2026-03-30 05:00:00",  # 3 consecutive missing hours (02:00, 03:00, 04:00)
            ],
            "value": [10.0, 40.0, 100.0, 500.0],
        }
    )

    clean_df = process_sensor_timeseries(raw_data)
    print(clean_df.to_string(index=False))