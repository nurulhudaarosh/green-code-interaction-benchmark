import csv
import math
from collections import defaultdict
from datetime import datetime

class ExpenseAnalyzer:
    # Sentinel: user didn't pass a threshold → disable filtering
    _NO_FILTER = None

    def __init__(self, min_amount=None):
        self.expenses = []
        self.errors = []
        self.min_amount = self._validate_min_amount(min_amount)

    # ---------- validation helpers ----------

    @staticmethod
    def _validate_min_amount(value):
        """Accepts None (disabled), 0, positive numbers. Rejects nan/inf/negatives."""
        if value is None:
            return None
        try:
            v = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"min_amount must be a number, got {value!r}")
        if math.isnan(v) or math.isinf(v):
            raise ValueError(f"min_amount must be finite, got {value!r}")
        if v < 0:
            raise ValueError(f"min_amount must be >= 0, got {value!r}")
        return v

    def set_min_amount(self, value):
        self.min_amount = self._validate_min_amount(value)

    def _passes_filter(self, amount):
        """None threshold → accept everything. Otherwise strict >= comparison."""
        if self.min_amount is None:
            return True
        return amount >= self.min_amount

    # ---------- parsing ----------

    def _parse_expense(self, date, category, amount, description=""):
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

        cleaned = str(amount).strip().replace("$", "").replace(",", "")
        try:
            amount_val = float(cleaned)
        except ValueError:
            raise ValueError(f"invalid amount '{amount}'")

        if math.isnan(amount_val) or math.isinf(amount_val):
            raise ValueError(f"non-finite amount '{amount}'")
        if amount_val < 0:
            raise ValueError(f"negative amount '{amount}'")

        return {
            "date": expense_date,
            "category": str(category).strip(),
            "amount": amount_val,
            "description": str(description).strip() if description else "",
        }

    def add_expense(self, date, category, amount, description="", strict=True):
        try:
            record = self._parse_expense(date, category, amount, description)
        except ValueError as e:
            self.errors.append({
                "raw": {"date": date, "category": category,
                        "amount": amount, "description": description},
                "reason": str(e),
                "type": "malformed",
            })
            if strict:
                raise
            return False

        if not self._passes_filter(record["amount"]):
            self.errors.append({
                "raw": record,
                "reason": f"below minimum (${self.min_amount:,.2f})",
                "type": "filtered",
            })
            return False

        self.expenses.append(record)
        return True

    def load_from_csv(self, filepath, strict=False):
        """Handles: missing file, empty file, header-only, blank rows, missing cols."""
        loaded = 0

        try:
            f = open(filepath, 'r', newline='', encoding='utf-8-sig')
        except FileNotFoundError:
            self.errors.append({"raw": {"filepath": filepath},
                                "reason": "file not found",
                                "type": "malformed"})
            return (0, 1)
        except OSError as e:
            self.errors.append({"raw": {"filepath": filepath},
                                "reason": f"cannot open file: {e}",
                                "type": "malformed"})
            return (0, 1)

        with f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                self.errors.append({"raw": {"filepath": filepath},
                                    "reason": "empty file / no header",
                                    "type": "malformed"})
                return (0, 1)

            reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

            for i, row in enumerate(reader, start=2):
                # skip blank rows (any mix of None / empty strings)
                if not row or all(
                    v is None or str(v).strip() == "" for v in row.values()
                ):
                    continue
                try:
                    ok = self.add_expense(
                        row.get("date"), row.get("category"),
                        row.get("amount"), row.get("description", ""),
                        strict=False,
                    )
                    if ok:
                        loaded += 1
                except Exception as e:
                    self.errors.append({
                        "raw": row,
                        "reason": f"row {i}: unexpected error: {e}",
                        "type": "malformed",
                    })

        return (loaded, len(self.errors))

    # ---------- reporting ----------

    def report_errors(self, show_filtered=True):
        malformed = [e for e in self.errors if e.get("type") == "malformed"]
        filtered = [e for e in self.errors if e.get("type") == "filtered"]

        if malformed:
            print(f"\n{len(malformed)} malformed record(s) rejected:")
            print("-" * 60)
            for i, err in enumerate(malformed, 1):
                print(f"  [{i}] reason: {err['reason']}")
                print(f"      raw:    {err['raw']}")

        if filtered and show_filtered:
            print(f"\n{len(filtered)} record(s) filtered out "
                  f"(< ${self.min_amount:,.2f}):")
            print("-" * 60)
            for i, err in enumerate(filtered, 1):
                r = err["raw"]
                print(f"  [{i}] {r['date'].strftime('%Y-%m-%d')}  "
                      f"{r['category']:<12} ${r['amount']:>9,.2f}  "
                      f"{r['description']}")

        if not malformed and not filtered:
            print("No malformed or filtered records.")

    # ---------- analytics (all boundary-safe) ----------

    def total(self):
        return sum(e["amount"] for e in self.expenses)  # 0.0 on empty

    def average(self):
        return self.total() / len(self.expenses) if self.expenses else 0.0

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
        if n is None or n <= 0:      # guard n=0, negative, None
            return []
        return sorted(self.expenses, key=lambda x: -x["amount"])[:n]

    def summary(self):
        if not self.expenses:
            print("=" * 50)
            print("EXPENSE ANALYZER SUMMARY")
            print("=" * 50)
            print("No valid expenses recorded.")
            self.report_errors()
            print("=" * 50)
            return

        malformed = sum(1 for e in self.errors if e.get("type") == "malformed")
        filtered = sum(1 for e in self.errors if e.get("type") == "filtered")
        thresh = "disabled" if self.min_amount is None else f"${self.min_amount:,.2f}"

        print("=" * 50)
        print("EXPENSE ANALYZER SUMMARY")
        print("=" * 50)
        print(f"Minimum amount filter: {thresh}")
        print(f"Valid expenses:        {len(self.expenses)}")
        if malformed:
            print(f"Malformed rejected:    {malformed}")
        if filtered:
            print(f"Filtered (< min):      {filtered}")
        print(f"Total amount:          ${self.total():,.2f}")
        print(f"Average:               ${self.average():,.2f}")

        print("\n--- By Category ---")
        total = self.total()
        for cat, amt in self.by_category().items():
            pct = (amt / total) * 100 if total else 0.0
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


# ---------------- demo / self-test ----------------

def _run_case(label, fn):
    print(f"\n### {label} ###")
    try:
        fn()
    except Exception as e:
        print(f"  !! unexpected exception: {type(e).__name__}: {e}")


if __name__ == "__main__":

    def case_empty():
        a = ExpenseAnalyzer()
        a.summary()                      # should not crash, prints "No valid..."

    def case_zero_min():
        a = ExpenseAnalyzer(min_amount=0)
        a.add_expense("2024-01-01", "Food", "0.00", "Free sample")
        a.add_expense("2024-01-02", "Food", "0.01", "Penny")
        a.summary()                      # both pass (>= 0)

    def case_boundary_filter():
        a = ExpenseAnalyzer(min_amount=40.00)
        a.add_expense("2024-01-01", "Food", "39.99", "Just under")
        a.add_expense("2024-01-02", "Food", "40.00", "Exactly at threshold")
        a.add_expense("2024-01-03", "Food", "40.01", "Just over")
        a.summary()                      # only 40.00 and 40.01 kept

    def case_bad_thresholds():
        for bad in [-1, float('nan'), float('inf'), "abc", object()]:
            try:
                ExpenseAnalyzer(min_amount=bad)
                print(f"  !! should have rejected min_amount={bad!r}")
            except ValueError as e:
                print(f"  rejected min_amount={bad!r}: {e}")

    def case_nan_amount():
        a = ExpenseAnalyzer()
        a.add_expense("2024-01-01", "Food", "nan", "NaN amount", strict=False)
        a.add_expense("2024-01-02", "Food", "inf", "Inf amount", strict=False)
        a.add_expense("2024-01-03", "Food", "0",   "Zero (ok)")
        a.summary()

    def case_top_n_boundaries():
        a = ExpenseAnalyzer()
        for i, amt in enumerate([10, 20, 30], start=1):
            a.add_expense(f"2024-01-0{i}", "X", str(amt))
        print("  top_expenses()        ->", [e["amount"] for e in a.top_expenses()])
        print("  top_expenses(0)       ->", [e["amount"] for e in a.top_expenses(0)])
        print("  top_expenses(-3)      ->", [e["amount"] for e in a.top_expenses(-3)])
        print("  top_expenses(None)    ->", [e["amount"] for e in a.top_expenses(None)])
        print("  top_expenses(100)     ->", [e["amount"] for e in a.top_expenses(100)])

    def case_missing_file():
        a = ExpenseAnalyzer()
        a.load_from_csv("/tmp/definitely_not_here_12345.csv")
        a.summary()

    def case_header_only_csv(tmp="/tmp/_hdr_only.csv"):
        with open(tmp, "w") as f:
            f.write("date,category,amount,description\n")
        a = ExpenseAnalyzer()
        a.load_from_csv(tmp)
        a.summary()

    def case_blank_rows_csv(tmp="/tmp/_blanks.csv"):
        with open(tmp, "w") as f:
            f.write("date,category,amount,description\n")
            f.write("2024-01-01,Food,10,Lunch\n")
            f.write(",,,\n")                    # blank row
            f.write("   ,   ,   ,   \n")        # whitespace-only row
            f.write("2024-01-02,Food,20,Dinner\n")
        a = ExpenseAnalyzer()
        a.load_from_csv(tmp)
        a.summary()

    _run_case("Empty analyzer", case_empty)
    _run_case("min_amount=0 (accepts zero/penny)", case_zero_min)
    _run_case("Filter boundary: 39.99 / 40.00 / 40.01", case_boundary_filter)
    _run_case("Invalid thresholds", case_bad_thresholds)
    _run_case("NaN / Inf / zero amounts", case_nan_amount)
    _run_case("top_expenses() boundary values", case_top_n_boundaries)
    _run_case("Missing file", case_missing_file)
    _run_case("Header-only CSV", case_header_only_csv)
    _run_case("CSV with blank rows", case_blank_rows_csv)