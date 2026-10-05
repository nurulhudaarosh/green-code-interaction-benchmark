import pandas as pd


def process_sensor_readings(df: pd.DataFrame) -> pd.DataFrame:
    """Sorts sensor readings, fills interior hourly gaps using linear interpolation,

    marks inserted rows, and returns a deterministic DataFrame.

    Expected input columns: 'sensor_id', 'timestamp', 'value'
    """
    # Ensure correct data types
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    processed_groups = []

    # Sort deterministically upfront by sensor_id and timestamp
    for sensor_id, group in df.sort_values(
        by=["sensor_id", "timestamp"]
    ).groupby("sensor_id"):
        # Remove duplicate timestamps per sensor if any exist
        group = group.drop_duplicates(subset=["timestamp"])

        if group.empty:
            continue

        # Set timestamp index for hourly resampling across interior range
        group = group.set_index("timestamp")

        # Create complete hourly grid from min to max timestamp for this sensor
        full_index = pd.date_range(
            start=group.index.min(), end=group.index.max(), freq="h", name="timestamp"
        )

        # Reindex to reveal missing interior timestamps
        resampled = group.reindex(full_index)

        # Mark interpolated rows (rows that were not present in the original dataset)
        resampled["is_interpolated"] = resampled["sensor_id"].isna()

        # Fill metadata
        resampled["sensor_id"] = sensor_id

        # Perform linear interpolation on missing interior values
        resampled["value"] = resampled["value"].interpolate(method="linear")

        processed_groups.append(resampled.reset_index())

    if not processed_groups:
        return pd.DataFrame(
            columns=["sensor_id", "timestamp", "value", "is_interpolated"]
        )

    # Combine and enforce deterministic sort order: sensor_id ASC, timestamp ASC
    result = pd.concat(processed_groups, ignore_index=True)
    result = result.sort_values(
        by=["sensor_id", "timestamp"], ascending=[True, True]
    ).reset_index(drop=True)

    # Return strict column ordering
    return result[["sensor_id", "timestamp", "value", "is_interpolated"]]


if __name__ == "__main__":
    # Example usage / Sanity check
    data = [
        {"sensor_id": "S1", "timestamp": "2026-03-01 10:00:00", "value": 10.0},
        {
            "sensor_id": "S1",
            "timestamp": "2026-03-01 13:00:00",
            "value": 25.0,
        },  # Gaps at 11:00, 12:00
        {"sensor_id": "S2", "timestamp": "2026-03-01 08:00:00", "value": 100.0},
        {"sensor_id": "S2", "timestamp": "2026-03-01 09:00:00", "value": 110.0},
    ]

    input_df = pd.DataFrame(data)
    output_df = process_sensor_readings(input_df)
    print(output_df)