import pandas as pd


def process_sensor_readings(df: pd.DataFrame) -> pd.DataFrame:
    """Sorts sensor readings, linearly interpolates missing interior hourly timestamps,

    marks inserted rows, and generates deterministic output.

    Expected input columns: 'sensor_id', 'timestamp', 'value'
    """
    # Ensure correct data types
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    processed_groups = []

    # Sort groups deterministically by sensor_id
    for sensor_id, group in sorted(df.groupby("sensor_id")):
        # Remove duplicates by timestamp, keeping the last reading, and sort by time
        group = group.drop_duplicates(subset=["timestamp"], keep="last").sort_values(
            "timestamp"
        )

        if len(group) == 0:
            continue

        # Set index for hourly resampling between min and max timestamp (interior only)
        group = group.set_index("timestamp")
        min_time, max_time = group.index.min(), group.index.max()

        # Create continuous hourly grid spanning the sensor's interior time range
        full_grid = pd.date_range(start=min_time, end=max_time, freq="1h", name="timestamp")

        # Reindex to insert missing hourly timestamps
        reindexed = group.reindex(full_grid)

        # Mark which rows were newly inserted
        reindexed["is_interpolated"] = reindexed["sensor_id"].isna()

        # Fill sensor_id for inserted rows
        reindexed["sensor_id"] = sensor_id

        # Linearly interpolate missing numeric values across time
        reindexed["value"] = reindexed["value"].interpolate(method="time")

        # Reset index to restore timestamp column
        processed_groups.append(reindexed.reset_index())

    if not processed_groups:
        return pd.DataFrame(
            columns=["sensor_id", "timestamp", "value", "is_interpolated"]
        )

    # Combine all groups and apply deterministic sorting
    result = pd.concat(processed_groups, ignore_index=True)
    result = result.sort_values(by=["sensor_id", "timestamp"]).reset_index(drop=True)

    # Enforce explicit column order
    return result[["sensor_id", "timestamp", "value", "is_interpolated"]]