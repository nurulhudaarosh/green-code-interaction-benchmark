import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Transaction:
    id: str
    amount: float
    category: str
    date: datetime


@dataclass
class AnalysisResult:
    valid_count: int = 0
    invalid_count: int = 0
    total_amount: float = 0.0
    by_category: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)

    @property
    def average_amount(self) -> float:
        return self.total_amount / self.valid_count if self.valid_count else 0.0


class TransactionAnalyzer:
    """
    Parses and analyzes raw transaction records.

    Each record is expected to be a dict with keys:
        id, amount, category, date (YYYY-MM-DD)

    Malformed records (missing fields, bad types, unparsable
    amounts/dates) are skipped and recorded in result.errors
    rather than raising or silently corrupting totals.
    """

    REQUIRED_FIELDS = ("id", "amount", "category", "date")
    DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S")

    def analyze(self, records: list[dict[str, Any]]) -> AnalysisResult:
        result = AnalysisResult()

        for idx, raw in enumerate(records):
            try:
                txn = self._parse_record(raw)
            except (ValueError, TypeError, KeyError) as exc:
                result.invalid_count += 1
                result.errors.append({"index": idx, "record": raw, "reason": str(exc)})
                continue

            result.valid_count += 1
            result.total_amount += txn.amount
            result.by_category[txn.category] = (
                result.by_category.get(txn.category, 0.0) + txn.amount
            )

        return result

    def _parse_record(self, raw: Any) -> Transaction:
        if not isinstance(raw, dict):
            raise TypeError(f"record is not a dict: {type(raw).__name__}")

        missing = [f for f in self.REQUIRED_FIELDS if f not in raw]
        if missing:
            raise KeyError(f"missing field(s): {', '.join(missing)}")

        txn_id = str(raw["id"]).strip()
        if not txn_id:
            raise ValueError("id is empty")

        amount = self._parse_amount(raw["amount"])

        category = raw["category"]
        if not isinstance(category, str) or not category.strip():
            raise ValueError(f"invalid category: {category!r}")
        category = category.strip().lower()

        date = self._parse_date(raw["date"])

        return Transaction(id=txn_id, amount=amount, category=category, date=date)

    def _parse_amount(self, raw_amount: Any) -> float:
        if isinstance(raw_amount, bool):
            # bool is a subclass of int in Python; explicitly reject it
            raise ValueError(f"amount must be numeric, got bool: {raw_amount!r}")

        if isinstance(raw_amount, (int, float)):
            amount = float(raw_amount)
        elif isinstance(raw_amount, str):
            cleaned = re.sub(r"[,$\s]", "", raw_amount)
            if not cleaned or not re.match(r"^-?\d+(\.\d+)?$", cleaned):
                raise ValueError(f"unparsable amount string: {raw_amount!r}")
            amount = float(cleaned)
        else:
            raise ValueError(f"amount must be numeric or string, got {type(raw_amount).__name__}")

        if amount < 0:
            raise ValueError(f"amount cannot be negative: {amount}")
        if amount != amount:  # NaN check
            raise ValueError("amount is NaN")

        return amount

    def _parse_date(self, raw_date: Any) -> datetime:
        if isinstance(raw_date, datetime):
            return raw_date
        if not isinstance(raw_date, str) or not raw_date.strip():
            raise ValueError(f"invalid date value: {raw_date!r}")

        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(raw_date.strip(), fmt)
            except ValueError:
                continue
        raise ValueError(f"unparsable date: {raw_date!r}")


if __name__ == "__main__":
    sample_records = [
        {"id": "t1", "amount": "1,200.50", "category": "Groceries", "date": "2026-01-15"},
        {"id": "t2", "amount": 45.0, "category": "gas", "date": "01/20/2026"},
        {"id": "t3", "amount": "not-a-number", "category": "gas", "date": "2026-01-21"},  # malformed
        {"id": "", "amount": 10.0, "category": "misc", "date": "2026-01-22"},  # malformed
        {"amount": 10.0, "category": "misc", "date": "2026-01-22"},  # malformed (missing id)
        {"id": "t6", "amount": -5.0, "category": "refund", "date": "2026-01-23"},  # malformed
        "not-a-dict",  # malformed
        {"id": "t8", "amount": 99.99, "category": "dining", "date": "2026-01-24"},
    ]

    analyzer = TransactionAnalyzer()
    result = analyzer.analyze(sample_records)

    print(f"Valid: {result.valid_count}, Invalid: {result.invalid_count}")
    print(f"Total: {result.total_amount:.2f}, Average: {result.average_amount:.2f}")
    print("By category:", result.by_category)
    print("Errors:")
    for err in result.errors:
        print(f"  [{err['index']}] {err['reason']}")