import json
from collections import defaultdict
from datetime import datetime


class ExpenseAnalyzer:
    """A lightweight, zero-dependency expense analyzer.

    Processes structured expense logs to compute totals, track budgets,
    and categorize spending habits.
    """

    def __init__(self, currency: str = "$"):
        self.currency = currency
        self.expenses = []
        self.budgets = {}

    def add_expense(
        self, amount: float, category: str, description: str, date: str = None
    ) -> dict:
        """Add a single expense transaction."""
        if amount <= 0:
            raise ValueError("Expense amount must be greater than zero.")

        parsed_date = date if date else datetime.now().strftime("%Y-%m-%d")

        expense = {
            "id": len(self.expenses) + 1,
            "amount": round(float(amount), 2),
            "category": category.strip().capitalize(),
            "description": description.strip(),
            "date": parsed_date,
        }
        self.expenses.append(expense)
        return expense

    def set_budget(self, category: str, limit: float) -> None:
        """Set a spending threshold for a specific category."""
        self.budgets[category.strip().capitalize()] = float(limit)

    def total_spending(() -> float:
        """Calculate total spend across all recorded expenses."""
        return sum(e["amount"] for e in self.expenses)

    def spending_by_category(self) -> dict:
        """Group and total spending by category."""
        totals = defaultdict(float)
        for e in self.expenses:
            totals[e["category"]] += e["amount"]
        return dict(totals)

    def budget_status(self) -> dict:
        """Compare actual spending against defined category budgets."""
        spending = self.spending_by_category()
        status = {}

        for category, limit in self.budgets.items():
            spent = spending.get(category, 0.0)
            remaining = limit - spent
            status[category] = {
                "budget": limit,
                "spent": spent,
                "remaining": remaining,
                "exceeded": spent > limit,
            }
        return status

    def summary_report(self) -> str:
        """Generate a human-readable summary of overall financial status."""
        total = self.total_spending()
        by_cat = self.spending_by_category()
        b_status = self.budget_status()

        lines = [
            "=" * 40,
            "         EXPENSE ANALYZER REPORT",
            "=" * 40,
            f"Total Expenses: {self.currency}{total:,.2f}",
            "-" * 40,
            "Breakdown by Category:",
        ]

        for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
            pct = (amt / total * 100) if total > 0 else 0
            lines.append(
                f"  - {cat:<15}: {self.currency}{amt:>8.2f} ({pct:>5.1f}%)"
            )

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


# Demonstration of core workflow
if __name__ == "__main__":
    analyzer = ExpenseAnalyzer(currency="$")

    # Set up budgets
    analyzer.set_budget("Groceries", 300.00)
    analyzer.set_budget("Dining", 150.00)
    analyzer.set_budget("Utilities", 200.00)

    # Log sample expenses
    analyzer.add_expense(120.50, "groceries", "Weekly grocery run", "2026-09-01")
    analyzer.add_expense(45.00, "dining", "Dinner with friends", "2026-09-02")
    analyzer.add_expense(185.20, "utilities", "Electricity bill", "2026-09-05")
    analyzer.add_expense(210.00, "groceries", "Bulk store restock", "2026-09-10")
    analyzer.add_expense(12.50, "coffee", "Morning latte", "2026-09-12")

    print(analyzer.summary_report())