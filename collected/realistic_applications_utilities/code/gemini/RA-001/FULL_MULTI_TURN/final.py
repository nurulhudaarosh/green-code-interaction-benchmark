import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class ExpenseAnalyzer:
    """A robust expense analyzer capable of handling empty datasets, zero thresholds,

    extreme numbers, floating-point precision, and non-standard boundaries.
    """

    def __init__(self, currency: str = "$"):
        self.currency = currency
        self.expenses: List[Dict[str, Any]] = []
        self.budgets: Dict[str, float] = {}
        self.rejected_records: List[Tuple[Any, str]] = []

    def validate_record(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize a raw expense record with strict boundary checking."""
        if not isinstance(raw_data, dict):
            raise ValueError(
                f"Record must be a dictionary, got {type(raw_data).__name__}"
            )

        # Validate Amount (Must be a finite positive float > 0)
        if "amount" not in raw_data or raw_data.get("amount") is None:
            raise ValueError("Missing required field 'amount'")

        try:
            amount = float(raw_data["amount"])
        except (ValueError, TypeError):
            raise ValueError(f"Invalid amount value: {raw_data['amount']!r}")

        # Check float non-finites (NaN, Inf) and negative boundaries
        if (
            amount != amount
            or amount == float("inf")
            or amount == float("-inf")
        ):
            raise ValueError(f"Amount must be a finite number, got {amount}")
        if amount <= 0:
            raise ValueError(f"Amount must be strictly positive (> 0), got {amount}")

        # Validate Category (Handle empty strings, whitespace-only, non-string types)
        raw_category = raw_data.get("category")
        if raw_category is None or not str(raw_category).strip():
            category = "Uncategorized"
        else:
            category = str(raw_category).strip().capitalize()

        # Validate Description (Handle empty, null, or whitespace-only inputs)
        raw_description = raw_data.get("description")
        if raw_description is None or not str(raw_description).strip():
            description = "N/A"
        else:
            description = str(raw_description).strip()

        # Validate Date Format (YYYY-MM-DD or default to today if empty/missing)
        raw_date = raw_data.get("date")
        if raw_date is None or not str(raw_date).strip():
            date_str = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                date_str = datetime.strptime(
                    str(raw_date).strip(), "%Y-%m-%d"
                ).strftime("%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid date format: {raw_date!r}. Expected YYYY-MM-DD"
                )

        return {
            "id": len(self.expenses) + 1,
            "amount": round(amount, 2),
            "category": category,
            "description": description,
            "date": date_str,
        }

    def add_expense(
        self,
        amount: Any,
        category: str = "Uncategorized",
        description: str = "N/A",
        date: Optional[str] = None,
    ) -> Optional[dict]:
        """Safely add a single expense record, logging and storing if malformed."""
        raw_record = {
            "amount": amount,
            "category": category,
            "description": description,
            "date": date,
        }
        try:
            validated = self.validate_record(raw_record)
            self.expenses.append(validated)
            return validated
        except ValueError as err:
            logging.warning(f"Rejected record {raw_record}: {err}")
            self.rejected_records.append((raw_record, str(err)))
            return None

    def ingest_batch(
        self, records: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, int]:
        """Batch-process a list of raw expense records safely, handling empty/None inputs."""
        if not records:
            return {"processed": 0, "rejected": 0}

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

    def filter_expenses(self, min_amount: float = 0.0) -> List[Dict[str, Any]]:
        """Return valid expenses >= min_amount.

        Ensures non-negative thresholds and floats.
        """
        # Clamp min_amount to 0 if negative, or handle zero boundary explicitly
        effective_min = max(0.0, float(min_amount or 0.0))
        return [e for e in self.expenses if e["amount"] >= effective_min]

    def set_budget(self, category: str, limit: float) -> None:
        """Set a spending limit for a specific category, allowing 0 for strict caps."""
        if limit is None or limit < 0:
            raise ValueError("Budget limit must be a non-negative number.")

        cat_key = (
            "Uncategorized"
            if not category or not str(category).strip()
            else str(category).strip().capitalize()
        )
        self.budgets[cat_key] = float(limit)

    def total_spending(self, min_amount: float = 0.0) -> float:
        """Calculate total spending, safely returning 0.0 for empty sets."""
        filtered = self.filter_expenses(min_amount=min_amount)
        if not filtered:
            return 0.0
        return round(sum(e["amount"] for e in filtered), 2)

    def spending_by_category(
        self, min_amount: float = 0.0
    ) -> Dict[str, float]:
        """Group spending by category with safe aggregation for empty datasets."""
        totals = defaultdict(float)
        for e in self.filter_expenses(min_amount=min_amount):
            totals[e["category"]] += e["amount"]
        return {cat: round(amt, 2) for cat, amt in totals.items()}

    def budget_status(self, min_amount: float = 0.0) -> Dict[str, dict]:
        """Compare actual spending against defined budgets, handling zero-budget boundaries."""
        spending = self.spending_by_category(min_amount=min_amount)
        status = {}
        for category, limit in self.budgets.items():
            spent = spending.get(category, 0.0)
            remaining = limit - spent
            status[category] = {
                "budget": limit,
                "spent": spent,
                "remaining": round(remaining, 2),
                "exceeded": spent > limit,
            }
        return status

    def summary_report(self, min_amount: float = 0.0) -> str:
        """Generate a complete text report, handling zero-match and empty dataset cases gracefully."""
        filtered_records = self.filter_expenses(min_amount=min_amount)
        total = self.total_spending(min_amount=min_amount)
        by_cat = self.spending_by_category(min_amount=min_amount)
        b_status = self.budget_status(min_amount=min_amount)

        lines = [
            "=" * 42,
            "          EXPENSE ANALYZER REPORT         ",
            "=" * 42,
            f"Min Amount Filter : {self.currency}{min_amount:,.2f}",
            f"Matching Records  : {len(filtered_records)} / {len(self.expenses)}",
            f"Malformed Records : {len(self.rejected_records)}",
            f"Total Expenses    : {self.currency}{total:,.2f}",
            "-" * 42,
            "Breakdown by Category:",
        ]

        if not by_cat:
            lines.append("  (No transactions meet the filter criteria)")
        else:
            for cat, amt in sorted(
                by_cat.items(), key=lambda x: x[1], reverse=True
            ):
                # Avoid ZeroDivisionError if total is 0.0
                pct = (amt / total * 100) if total > 0 else 0.0
                lines.append(
                    f"  - {cat:<15}: {self.currency}{amt:>8.2f} ({pct:>5.1f}%)"
                )

        if b_status:
            lines.extend(["-" * 42, "Budget Health:"])
            for cat, data in b_status.items():
                flag = " [OVER BUDGET!]" if data["exceeded"] else ""
                lines.append(
                    f"  - {cat:<15}: {self.currency}{data['spent']:>7.2f} / "
                    f"{self.currency}{data['budget']:>7.2f}{flag}"
                )

        lines.append("=" * 42)
        return "\n".join(lines)


# Demonstration testing empty sets and boundary conditions
if __name__ == "__main__":
    analyzer = ExpenseAnalyzer(currency="$")

    # 1. Empty State Test
    print("--- Test 1: Empty Dataset Summary ---")
    print(analyzer.summary_report())

    # 2. Ingest Empty List & None Inputs
    analyzer.ingest_batch([])
    analyzer.ingest_batch(None)

    # 3. Boundary & Extreme Value Tests
    boundary_dataset = [
        # Micro transaction boundary
        {
            "amount": 0.01,
            "category": "Micro",
            "description": "1 cent",
            "date": "2026-09-01",
        },
        # Zero amount boundary (Should fail validation)
        {"amount": 0.00, "category": "Free", "description": "Zero cost item"},
        # NaN / Infinity boundary (Should fail validation)
        {"amount": float("nan"), "category": "Error", "description": "NaN test"},
        {"amount": float("inf"), "category": "Error", "description": "Inf test"},
        # Missing / Whitespace fields
        {
            "amount": 50.00,
            "category": "   ",
            "description": "  ",
            "date": "   ",
        },
        # Zero-budget constraint test
        {
            "amount": 10.00,
            "category": "StrictCap",
            "description": "Exceeds $0 budget",
        },
    ]

    analyzer.set_budget("StrictCap", 0.00)  # $0 threshold budget
    analyzer.ingest_batch(boundary_dataset)

    print("\n--- Test 2: Summary After Processing Boundary Data ---")
    print(analyzer.summary_report())

    print("\n--- Test 3: High Filter Threshold (Matches Nothing) ---")
    print(analyzer.summary_report(min_amount=1000.00))