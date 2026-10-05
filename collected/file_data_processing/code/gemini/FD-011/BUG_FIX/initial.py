import pandas as pd


def process_sensor_timeseries(
    df: pd.DataFrame,
    sensor_col: str = "sensor_id",
    time_col: str = "timestamp",
    val_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Sorts sensor time-series data, linearly interpolates missing hourly timestamps,

    and marks interpolated rows.
    """
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])

    if val_cols is None:
        val_cols = [
            col for col in df.columns if col not in (sensor_col, time_col)
        ]

    # Ensure sorting before grouped operation
    df = df.sort_values([sensor_col, time_col]).reset_index(drop=True)

    processed_groups = []

    for sensor_id, group in df.groupby(sensor_col, sort=True):
        # Drop duplicates on timestamp within the sensor, keeping first
        group = group.drop_duplicates(subset=[time_col])

        # Set index to datetime for resampling
        group = group.set_index(time_col)

        # Resample to strict hourly grid covering [min_time, max_time]
        resampled = group.resample("1h").asfreq()

        # Identify inserted rows (where original sensor_id is NaN due to reindexing)
        is_inserted = resampled[sensor_col].isna()

        # Fill sensor_id and mark inserted status
        resampled[sensor_col] = sensor_id
        resampled["is_interpolated"] = is_inserted

        # Linearly interpolate missing numeric values across missing interior hours
        resampled[val_cols] = resampled[val_cols].interpolate(
            method="linear", limit_area="inside"
        )

        processed_groups.append(resampled.reset_index())

    # Concatenate all sensor groups
    result = pd.concat(processed_groups, ignore_index=True)

    # Enforce deterministic column order and row sorting
    output_cols = [
        sensor_col,
        time_col,
        "is_interpolated",
    ] + val_cols
    result = result[output_cols].sort_values(
        [sensor_col, time_col], ignore_index=True
    )

    return result


if __name__ == "__main__":
    # Example usage / Verification
    raw_data = pd.DataFrame(
        {
            "sensor_id": ["A", "A", "A", "B", "B"],
            "timestamp": [
                "2026-03-01 08:00:00",
                "2026-03-01 11:00:00",  # Missing 09:00 and 10:00 for A
                "2026-03-01 12:00:00",
                "2026-03-01 09:00:00",
                "2026-03-01 10:00:00",  # Complete sequence for B
            ],
            "reading": [10.0, 25.0, 30.0, 5.0, 7.0],
        }
    )

    clean_df = process_sensor_timeseries(
        raw_data,
        sensor_col="sensor_id",
        time_col="timestamp",
        val_cols=["reading"],
    )
    print(clean_df.to_string(index=False))