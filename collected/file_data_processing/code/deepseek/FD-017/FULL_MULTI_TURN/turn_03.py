import pandas as pd


class EventPivotUtility:
    """
    Validates event records, aggregates counts by (date, region),
    derives deterministic event-type columns (every observed event type),
    fills missing cells with zero, and sorts rows.
    """

    REQUIRED_COLUMNS = {"date", "region", "event_type"}

    def __init__(self, records):
        if not isinstance(records, list):
            raise TypeError("records must be a list of dictionaries")
        self.records = records
        self.df = None
        self.pivot = None

    # ---------- validation ----------
    def validate(self):
        cleaned = []
        for i, rec in enumerate(self.records):
            if not isinstance(rec, dict):
                raise ValueError(f"Record at index {i} is not a dict: {rec!r}")

            missing = self.REQUIRED_COLUMNS - rec.keys()
            if missing:
                raise ValueError(
                    f"Record at index {i} missing required keys: {sorted(missing)}"
                )

            date = rec["date"]
            region = rec["region"]
            event_type = rec["event_type"]

            if date is None or (isinstance(date, float) and pd.isna(date)):
                raise ValueError(f"Record at index {i} has null date")
            if region is None or (isinstance(region, float) and pd.isna(region)):
                raise ValueError(f"Record at index {i} has null region")
            if event_type is None or (
                isinstance(event_type, float) and pd.isna(event_type)
            ):
                raise ValueError(f"Record at index {i} has null event_type")

            try:
                parsed_date = pd.to_datetime(date, errors="raise").normalize()
            except Exception as e:
                raise ValueError(
                    f"Record at index {i} has invalid date {date!r}: {e}"
                )

            cleaned.append(
                {
                    "date": parsed_date,
                    "region": str(region).strip(),
                    "event_type": str(event_type).strip(),
                }
            )

        if not cleaned:
            raise ValueError("No valid records to process")

        self.df = pd.DataFrame(cleaned)
        return self

    # ---------- aggregation + pivot ----------
    def build_pivot(self):
        if self.df is None:
            raise RuntimeError("Call validate() before build_pivot()")

        # every observed event type becomes a column (deterministic order)
        event_types = sorted(self.df["event_type"].unique().tolist())

        # count occurrences of each (date, region, event_type)
        counts = (
            self.df.groupby(["date", "region", "event_type"])
            .size()
            .rename("count")
            .reset_index()
        )

        # pivot so each event_type is its own column
        pivot = counts.pivot_table(
            index=["date", "region"],
            columns="event_type",
            values="count",
            aggfunc="sum",
            fill_value=0,
        )

        # guarantee every observed event type is a column, in sorted order
        pivot = pivot.reindex(columns=event_types, fill_value=0)

        # zero for any absent (date, region, event_type) combination
        pivot = pivot.fillna(0).astype(int)

        # stable sort by date then region
        pivot = pivot.sort_index(level=["date", "region"], sort_remaining=True)

        self.pivot = pivot
        return self

    # ---------- convenience ----------
    def to_records(self):
        if self.pivot is None:
            raise RuntimeError("Call build_pivot() before to_records()")
        return self.pivot.reset_index().to_dict(orient="records")

    def to_dataframe(self):
        if self.pivot is None:
            raise RuntimeError("Call build_pivot() before to_dataframe()")
        return self.pivot.reset_index()


def pivot_events(records):
    """One-shot helper: validate -> aggregate -> pivot -> sort."""
    return EventPivotUtility(records).validate().build_pivot().to_dataframe()


if __name__ == "__main__":
    sample = [
        {"date": "2024-01-01", "region": "NA", "event_type": "click"},
        {"date": "2024-01-01", "region": "NA", "event_type": "click"},
        {"date": "2024-01-01", "region": "NA", "event_type": "view"},
        {"date": "2024-01-01", "region": "EU", "event_type": "view"},
        {"date": "2024-01-02", "region": "EU", "event_type": "click"},
        {"date": "2024-01-02", "region": "NA", "event_type": "purchase"},
    ]

    result = pivot_events(sample)
    print(result)