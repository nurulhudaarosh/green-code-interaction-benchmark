import csv
import json
from collections import defaultdict
from datetime import datetime

class ExpenseAnalyzer:
    def __init__(self):
        self.expenses = []
        self.errors = []  # track rejected records

    def _parse_expense(self, date, category, amount, description=""):
        """Parse and validate a single record. Raises ValueError with reason."""
        if date is None or str(date).strip() == "":
            raise ValueError("missing date")
        if category is None or str(category).strip() == "":
            raise ValueError("missing category")
        if amount is None or str(amount).strip() == "":
            raise ValueError("missing amount")

        try:
            expense_date = datetime.strptime(str(date).strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"invalid date '{date}' (expected YYYY-MM-DD)")

        # strip currency symbols, commas, whitespace
        cleaned = str(amount).strip().replace("$", "").replace(",", "")
        try:
            amount_val = float(cleaned)
        except ValueError:
            raise ValueError(f"invalid amount '{amount}'")

        if amount_val < 0:
            raise ValueError(f"negative amount '{amount}'")

        return {
            "date": expense_date,
            "category": str(category).strip(),
            "amount": amount_val,
            "description": str(description).strip() if description else "",
        }

    def add_expense(self, date, category, amount, description="", strict=True):
        """
        Add a single expense. If strict=False, malformed records are logged
        to self.errors instead of raising.
        """
        try:
            record = self._parse_expense(date, category, amount, description)
        except ValueError as e:
            self.errors.append({
                "raw": {"date": date, "category": category,
                        "amount": amount, "description": description},
                "reason": str(e),
            })
            if strict:
                raise
            return False
        self.expenses.append(record)
        return True

    def load_from_csv(self, filepath, strict=False):
        """
        Load from CSV. Handles:
          - missing/blank rows
          - missing columns (KeyError)
          - malformed values
          - quoted commas / extra whitespace
        Returns (loaded_count, error_count).
        """
        loaded = 0
        with open(filepath, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                self.errors.append({"raw": None, "reason": "empty file / no header"})
                return (0, 1)

            # normalize headers
            reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

            for i, row in enumerate(reader, start=2):  # row 1 is header
                if not row or all((v is None or str(v).strip() == "") for v in row.values()):
                    continue  # skip blank lines silently

                try:
                    ok = self.add_expense(
                        row.get("date"),
                        row.get("category"),
                        row.get("amount"),
                        row.get("description", ""),
                        strict=False,
                    )
                    if ok:
                        loaded += 1
                except Exception as e:  # catch-all per-row safety
                    self.errors.append({
                        "raw": row, "reason": f"row {i}: unexpected error: {e}"
                    })

        return (loaded, len(self.errors))

    def report_errors(self):
        """Print a clear report of rejected records."""
        if not self.errors:
            print("No malformed records detected.")
            return
        print(f"\n{len(self.errors)} malformed record(s) rejected:")
        print("-" * 60)
        for i, err in enumerate(self.errors, 1):
            print(f"  [{i}] reason: {err['reason']}")
            print(f"      raw:    {err['raw']}")

    # --- analytics (unchanged behavior, now safe against bad data) ---

    def total(self):
        return sum(e["amount"] for e in self.expenses)

    def by_category(self):
        totals = defaultdict(float)
        for e in self.expenses:
            totals[e["category"]] += e["amount"]
        return dict(sorted(totals.items(), key=lambda x: -x[1]))

    def by_month(self):
        totals = defaultdict(float)
        for e in self.expenses:
            totals[e["date"].strftime("%Y-%m")] += e["amount"]
        return dict(sorted(totals.items()))

    def top_expenses(self, n=5):
        return sorted(self.expenses, key=lambda x: -x["amount"])[:n]

    def summary(self):
        if not self.expenses:
            print("No valid expenses recorded.")
            self.report_errors()
            return

        print("=" * 50)
        print("EXPENSE ANALYZER SUMMARY")
        print("=" * 50)
        print(f"Valid expenses: {len(self.expenses)}")
        if self.errors:
            print(f"Rejected:       {len(self.errors)}")
        print(f"Total amount:   ${self.total():,.2f}")
        print(f"Average:        ${self.total()/len(self.expenses):,.2f}")

        print("\n--- By Category ---")
        for cat, amt in self.by_category().items():
            pct = (amt / self.total()) * 100
            print(f"  {cat:<15} ${amt:>10,.2f}  ({pct:5.1f}%)")

        print("\n--- By Month ---")
        for month, amt in self.by_month().items():
            print(f"  {month}  ${amt:>10,.2f}")

        print("\n--- Top 5 Expenses ---")
        for e in self.top_expenses(5):
            print(f"  {e['date'].strftime('%Y-%m-%d')}  "
                  f"{e['category']:<12} ${e['amount']:>9,.2f}  {e['description']}")
        print("=" * 50)
        self.report_errors()


if __name__ == "__main__":
    analyzer = ExpenseAnalyzer()

    # Mix of good and bad records to exercise all failure modes
    records = [
        ("2024-01-05", "Food",           "45.20",  "Groceries"),
        ("2024-13-01", "Food",           "20.00",  "Bad month"),        # invalid date
        ("2024-01-12", "Transport",      "30.00",  "Gas"),
        ("2024-01-20", "Food",           "$62.75", "Restaurant"),       # $ stripped
        ("bad-date",   "Food",           "10.00",  "Bad date format"),
        ("2024-02-03", "Utilities",      "1,200",  "Electric bill"),    # comma stripped
        ("2024-02-14", "",               "85.50",  "Missing category"),
        ("2024-02-22", "Food",           "abc",    "Bad amount"),
        ("2024-03-01", "Transport",      "-5.00",  "Negative amount"),
        ("2024-03-15", "Utilities",      "",       "Missing amount"),
        ("2024-03-20", "Entertainment",  "50.00",  "Movie night"),
        (None,         "Food",           "15.00",  "Missing date"),
        ("2024-03-25", "Food",           None,     "Missing amount field"),
    ]

    for date, cat, amt, desc in records:
        analyzer.add_expense(date, cat, amt, desc, strict=False)

    analyzer.summary()