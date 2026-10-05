import pandas as pd


def process_sensor_readings(df: pd.DataFrame) -> pd.DataFrame:
    """Sorts input sensor readings chronologically before detecting gaps, fills every

    missing interior hourly timestamp (including consecutive missing hours) via linear

    interpolation without extrapolating before the first or after the last reading,

    marks inserted rows as 'filled', and returns a deterministic DataFrame.

    Expected input columns: 'sensor_id', 'timestamp', 'value'
    """
    if df.empty:
        return pd.DataFrame(
            columns=["sensor_id", "timestamp", "value", "is_interpolated"]
        )

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Sort input chronologically upfront across sensors and timestamps
    df = df.sort_values(
        by=["sensor_id", "timestamp"], ascending=[True, True]
    ).reset_index(drop=True)

    processed_groups = []

    for sensor_id, group in df.groupby("sensor_id", sort=True):
        group = group.sort_values(by="timestamp", ascending=True).drop_duplicates(
            subset=["timestamp"]
        )

        if group.empty:
            continue

        # Strict interior boundaries: start at min observation, end at max observation (no extrapolation)
        min_time = group["timestamp"].min()
        max_time = group["timestamp"].max()

        group = group.set_index("timestamp")

        # Generate continuous hourly sequence spanning from the first to the last reading
        full_index = pd.date_range(
            start=min_time, end=max_time, freq="h", name="timestamp"
        )

        resampled = group.reindex(full_index)

        # Mark rows: 'filled' for inserted hourly slots, 'original' for existing ones
        resampled["is_interpolated"] = resampled["sensor_id"].apply(
            lambda x: "filled" if pd.isna(x) else "original"
        )

        resampled["sensor_id"] = sensor_id

        # Linear interpolation handles consecutive NaNs natively inside interior bounds
        resampled["value"] = resampled["value"].interpolate(
            method="linear", limit_area="inside"
        )

        processed_groups.append(resampled.reset_index())

    if not processed_groups:
        return pd.DataFrame(
            columns=["sensor_id", "timestamp", "value", "is_interpolated"]
        )

    # Combine and enforce deterministic final ordering
    result = pd.concat(processed_groups, ignore_index=True)
    result = result.sort_values(
        by=["sensor_id", "timestamp"], ascending=[True, True]
    ).reset_index(drop=True)

    return result[["sensor_id", "timestamp", "value", "is_interpolated"]]


if __name__ == "__main__":
    # Test with out-of-order timestamps and multiple consecutive missing hours
    test_data = [
        {
            "sensor_id": "S1",
            "timestamp": "2026-03-01 14:00:00",
            "value": 50.0,
        },  # Gap of 3 consecutive hours (11:00, 12:00, 13:00)
        {"sensor_id": "S1", "timestamp": "2026-03-01 10:00:00", "value": 10.0},
        {"sensor_id": "S2", "timestamp": "2026-03-01 09:00:00", "value": 110.0},
        {"sensor_id": "S2", "timestamp": "2026-03-01 07:00:00", "value": 90.0},
    ]

    df_out = process_sensor_readings(pd.DataFrame(test_data))
    print(df_out)