from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Union


class RecordAnalyzer:
    """Analyzes and cleans datasets containing empty, malformed, zero-value,

    and whitespace-heavy records.
    """

    def __init__(self, data: List[Dict[str, Any]]) -> None:
        self.raw_data = data
        self.cleaned_records: List[Dict[str, Any]] = []
        self.malformed_records: List[Dict[str, Any]] = []
        self.empty_records: List[Dict[str, Any]] = []

        # Metrics
        self.zero_value_counts: Dict[str, int] = {}
        self.whitespace_cleaned_counts: Dict[str, int] = {}

    def _clean_value(self, key: str, value: Any) -> Any:
        """Strips whitespace, parses numeric strings, and tracks transformations."""
        if isinstance(value, str):
            stripped = value.strip()
            if stripped != value:
                self.whitespace_cleaned_counts[key] = (
                    self.whitespace_cleaned_counts.get(key, 0) + 1
                )
            value = stripped

            # Attempt numeric conversion for standard string numbers
            if value:
                try:
                    # Convert float or int strings cleanly
                    num = float(value)
                    value = int(num) if num.is_integer() else num
                except ValueError:
                    pass  # Keep as cleaned string if non-numeric

        return value

    def process(self) -> Dict[str, Any]:
        """Runs analysis, handling records across all target edge cases."""
        for index, record in enumerate(self.raw_data):
            # 1. Handle non-dict or structural malformations
            if not isinstance(record, dict):
                self.malformed_records.append(
                    {"index": index, "record": record, "reason": "Not a dict"}
                )
                continue

            cleaned_record = {}
            has_valid_content = False

            for k, v in record.items():
                cleaned_key = k.strip() if isinstance(k, str) else k
                cleaned_val = self._clean_value(cleaned_key, v)

                # Track zero-values (0, 0.0, "0")
                if cleaned_val == 0 or cleaned_val == 0.0:
                    self.zero_value_counts[cleaned_key] = (
                        self.zero_value_counts.get(cleaned_key, 0) + 1
                    )

                # Check if field has non-empty content
                if cleaned_val not in (None, ""):
                    has_valid_content = True

                cleaned_record[cleaned_key] = cleaned_val

            # 2. Handle completely empty/whitespace-only records
            if not record or not has_valid_content:
                self.empty_records.append(
                    {"index": index, "record": record}
                )
            else:
                self.cleaned_records.append(cleaned_record)

        return self.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        """Generates an aggregate analysis summary."""
        total = len(self.raw_data)
        return {
            "total_records": total,
            "valid_cleaned_count": len(self.cleaned_records),
            "empty_record_count": len(self.empty_records),
            "malformed_record_count": len(self.malformed_records),
            "zero_value_frequencies": self.zero_value_counts,
            "whitespace_stripped_frequencies": self.whitespace_cleaned_counts,
            "cleaned_data": self.cleaned_records,
            "quarantined_empty": self.empty_records,
            "quarantined_malformed": self.malformed_records,
        }


# ==========================================
# Execution & Verification with Test Dataset
# ==========================================

raw_dataset = [
    {"id": " 101 ", "name": " Alice ", "balance": "250.50", "score": 0},
    {},  # Fully empty
    {"id": "   ", "name": "\t\n", "balance": None},  # Whitespace-heavy (effectively empty)
    "NOT_A_DICTIONARY",  # Malformed structure
    {"id": 102, "name": "Bob", "balance": "0.00", "score": " 0 "},  # Zero-values & whitespace
    {"id": " 103 ", "name": "Charlie", "balance": "invalid_num"},  # Malformed field value preserved safely
]

analyzer = RecordAnalyzer(raw_dataset)
results = analyzer.process()

# Visual output breakdown
print(f"Total Processed: {results['total_records']}")
print(f"Valid Cleaned:   {results['valid_cleaned_count']}")
print(f"Empty Dropped:   {results['empty_record_count']}")
print(f"Malformed Flagged: {results['malformed_record_count']}\n")

print("Cleaned Data:")
for item in results["cleaned_data"]:
    print(" ", item)

print("\nZero Value Counts:", results["zero_value_frequencies"])
print("Whitespace Fixes:", results["whitespace_stripped_frequencies"])