import pandas as pd


def process_sensor_timeseries(
    df: pd.DataFrame,
    sensor_col: str = "sensor_id",
    time_col: str = "timestamp",
    val_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Sorts unsorted sensor readings chronologically per sensor, fills missing

    interior hourly timestamps using linear interpolation, marks inserted rows,
    and returns a deterministic DataFrame.
    """
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])

    if val_cols is None:
        val_cols = [
            col for col in df.columns if col not in (sensor_col, time_col)
        ]

    # Explicitly sort chronologically by sensor and timestamp up front
    df = df.sort_values(by=[sensor_col, time_col]).reset_index(drop=True)

    processed_groups = []

    for sensor_id, group in df.groupby(sensor_col, sort=True):
        # Handle duplicate timestamps within the same sensor by keeping the first occurrence
        group = group.drop_duplicates(subset=[time_col], keep="first")

        # Set datetime index to perform grid resampling
        group = group.set_index(time_col)

        # Resample to hourly intervals strictly covering min_time to max_time per sensor
        resampled = group.resample("1h").asfreq()

        # Identify inserted missing gap timestamps
        is_inserted = resampled[sensor_col].isna()

        # Restore sensor ID metadata and label interpolated rows
        resampled[sensor_col] = sensor_id
        resampled["is_interpolated"] = is_inserted

        # Linearly interpolate numeric values strictly within interior missing gaps
        resampled[val_cols] = resampled[val_cols].interpolate(
            method="linear", limit_area="inside"
        )

        processed_groups.append(resampled.reset_index())

    # Combine processed sensor blocks
    result = pd.concat(processed_groups, ignore_index=True)

    # Output deterministic column order and sorted order
    output_cols = [sensor_col, time_col, "is_interpolated"] + val_cols
    result = result[output_cols].sort_values(
        by=[sensor_col, time_col], ignore_index=True
    )

    return result


if __name__ == "__main__":
    # Example using unsorted input
    raw_data = pd.DataFrame(
        {
            "sensor_id": ["A", "B", "A", "A", "B"],
            "timestamp": [
                "2026-03-01 11:00:00",  # Out of order for A
                "2026-03-01 10:00:00",
                "2026-03-01 08:00:00",
                "2026-03-01 12:00:00",
                "2026-03-01 09:00:00",
            ],
            "reading": [25.0, 7.0, 10.0, 30.0, 5.0],
        }
    )

    clean_df = process_sensor_timeseries(
        raw_data,
        sensor_col="sensor_id",
        time_col="timestamp",
        val_cols=["reading"],
    )
    print(clean_df.to_string(index=False))