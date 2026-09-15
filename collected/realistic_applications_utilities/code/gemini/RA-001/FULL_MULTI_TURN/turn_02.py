import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class ExpenseAnalyzer:
    """An expense analyzer with robust error handling for malformed records."""

    def __init__(self, currency: str = "$"):
        self.currency = currency
        self.expenses: List[Dict[str, Any]] = []
        self.budgets: Dict[str, float] = {}
        self.rejected_records: List[Tuple[Any, str]] = []

    def validate_record(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize a raw record. Raises ValueError if unresolvable."""
        if not isinstance(raw_data, dict):
            raise ValueError(f"Record must be a dictionary, got {type(raw_data).__name__}")

        # Validate Amount
        raw_amount = raw_data.get("amount")
        if raw_amount is None:
            raise ValueError("Missing required field 'amount'")
        try:
            amount = float(raw_amount)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid amount value: {raw_amount!r}")
        if amount <= 0:
            raise ValueError(f"Amount must be strictly positive, got {amount}")

        # Validate Category
        raw_category = raw_data.get("category")
        if not raw_category or not str(raw_category).strip():
            category = "Uncategorized"
        else:
            category = str(raw_category).strip().capitalize()

        # Validate Description
        raw_description = raw_data.get("description")
        description = str(raw_description).strip() if raw_description else "N/A"

        # Validate Date Format (YYYY-MM-DD)
        raw_date = raw_data.get("date")
        if not raw_date:
            date_str = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                date_str = datetime.strptime(str(raw_date).strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Invalid date format: {raw_date!r}. Expected YYYY-MM-DD")

        return {
            "id": len(self.expenses) + 1,
            "amount": round(amount, 2),
            "category": category,
            "description": description,
            "date": date_str,
        }

    def add_expense(
        self, amount: Any, category: str = "Uncategorized", description: str = "N/A", date: Optional[str] = None
    ) -> Optional[dict]:
        """Safely add a single expense record, logging and storing if malformed."""
        raw_record = {"amount": amount, "category": category, "description": description, "date": date}
        try:
            validated = self.validate_record(raw_record)
            self.expenses.append(validated)
            return validated
        except ValueError as err:
            logging.warning(f"Rejected record {raw_record}: {err}")
            self.rejected_records.append((raw_record, str(err)))
            return None

    def ingest_batch(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """Batch-process a list of raw expense records safely."""
        success_count = 0
        failure_count = 0

        for item in records:
            try:
                validated = self.validate_record(item)
                self.expenses.append(validated)
                success_count += 1
            except ValueError as err:
                logging.warning(f"Batch rejection for record {item}: {err}")
                self.rejected_records.append((item, str(err)))
                failure_count += 1

        return {"processed": success_count, "rejected": failure_count}

    def set_budget(self, category: str, limit: float) -> None:
        """Set a spending threshold for a specific category."""
        if limit < 0:
            raise ValueError("Budget limit cannot be negative.")
        self.budgets[category.strip().capitalize()] = float(limit)

    def total_spending(self) -> float:
        """Calculate total spend across all successfully recorded expenses."""
        return sum(e["amount"] for e in self.expenses)

    def spending_by_category(self) -> Dict[str, float]:
        """Group and total spending by category."""
        totals = defaultdict(float)
        for e in self.expenses:
            totals[e["category"]] += e["amount"]
        return dict(totals)

    def budget_status(self) -> Dict[str, dict]:
        """Compare actual spending against defined category budgets."""
        spending = self.spending_by_category()
        status = {}
        for category, limit in self.budgets.items():
            spent = spending.get(category, 0.0)
            status[category] = {
                "budget": limit,
                "spent": spent,
                "remaining": limit - spent,
                "exceeded": spent > limit,
            }
        return status

    def summary_report(self) -> str:
        """Generate a summary including valid transactions and rejection statistics."""
        total = self.total_spending()
        by_cat = self.spending_by_category()
        b_status = self.budget_status()

        lines = [
            "=" * 40,
            "         EXPENSE ANALYZER REPORT",
            "=" * 40,
            f"Valid Records : {len(self.expenses)}",
            f"Failed Records: {len(self.rejected_records)}",
            f"Total Expenses: {self.currency}{total:,.2f}",
            "-" * 40,
            "Breakdown by Category:",
        ]

        for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
            pct = (amt / total * 100) if total > 0 else 0
            lines.append(f"  - {cat:<15}: {self.currency}{amt:>8.2f} ({pct:>5.1f}%)")

        if b_status:
            lines.extend(["-" * 40, "Budget Health:"])
            for cat, data in b_status.items():
                flag = " [OVER BUDGET!]" if data["exceeded"] else ""
                lines.append(
                    f"  - {cat:<15}: {self.currency}{data['spent']:>7.2f} / "
                    f"{self.currency}{data['budget']:>7.2f}{flag}"
                )

        lines.append("=" * 40)
        return "\n".join(lines)


# Demonstration of batch error handling
if __name__ == "__main__":
    analyzer = ExpenseAnalyzer(currency="$")
    analyzer.set_budget("Groceries", 300.00)

    # Ingest mix of valid and malformed data
    raw_data_stream = [
        {"amount": 120.50, "category": "groceries", "description": "Weekly run", "date": "2026-09-01"},
        {"amount": "45.50", "category": "dining", "description": "String amount handled", "date": "2026-09-02"},
        {"amount": -20.00, "category": "groceries", "description": "Negative amount"},  # Malformed
        {"amount": "invalid", "category": "utilities", "description": "Bad string amount"},  # Malformed
        {"amount": 80.00, "category": "", "description": "Empty category auto-filled", "date": "2026-09-03"},
        {"amount": 50.00, "category": "groceries", "description": "Bad date format", "date": "09/04/2026"},  # Malformed
        "not_a_dict_record",  # Malformed
    ]

    stats = analyzer.ingest_batch(raw_data_stream)
    print(f"\nIngestion Results: {stats}\n")
    print(analyzer.summary_report())