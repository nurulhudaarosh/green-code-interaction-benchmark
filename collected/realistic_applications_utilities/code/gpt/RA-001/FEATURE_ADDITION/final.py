from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class Transaction:
    date: str
    description: str
    category: str
    amount: float


class ExpenseAnalyzer:
    def __init__(self, transactions: Iterable[Transaction]):
        self.transactions = list(transactions)

    def filter_by_minimum_amount(
        self, minimum_amount: float
    ) -> list[Transaction]:
        """Return transactions whose amount is at least the minimum."""
        if minimum_amount < 0:
            raise ValueError("minimum_amount cannot be negative")

        return [
            transaction
            for transaction in self.transactions
            if transaction.amount >= minimum_amount
        ]

    def total_expenses(
        self, minimum_amount: Optional[float] = None
    ) -> float:
        transactions = self.transactions

        if minimum_amount is not None:
            transactions = self.filter_by_minimum_amount(minimum_amount)

        return sum(transaction.amount for transaction in transactions)

    def category_totals(
        self, minimum_amount: Optional[float] = None
    ) -> dict[str, float]:
        transactions = self.transactions

        if minimum_amount is not None:
            transactions = self.filter_by_minimum_amount(minimum_amount)

        totals: dict[str, float] = {}

        for transaction in transactions:
            totals[transaction.category] = (
                totals.get(transaction.category, 0.0)
                + transaction.amount
            )

        return totals

    def largest_expense(
        self, minimum_amount: Optional[float] = None
    ) -> Optional[Transaction]:
        transactions = self.transactions

        if minimum_amount is not None:
            transactions = self.filter_by_minimum_amount(minimum_amount)

        return max(
            transactions,
            key=lambda transaction: transaction.amount,
            default=None,
        )


def parse_transactions(records: Iterable[dict]) -> list[Transaction]:
    """Parse valid transaction records and ignore malformed records."""
    transactions: list[Transaction] = []

    for record in records:
        try:
            if not isinstance(record, dict):
                continue

            date = record.get("date")
            description = record.get("description")
            category = record.get("category")
            amount = record.get("amount")

            if not all(
                isinstance(value, str) and value.strip()
                for value in (date, description, category)
            ):
                continue

            amount = float(amount)

            if amount < 0:
                continue

            transactions.append(
                Transaction(
                    date=date.strip(),
                    description=description.strip(),
                    category=category.strip(),
                    amount=amount,
                )
            )

        except (TypeError, ValueError):
            continue

    return transactions


def main() -> None:
    records = [
        {
            "date": "2026-09-01",
            "description": "Coffee",
            "category": "Food",
            "amount": 120,
        },
        {
            "date": "2026-09-02",
            "description": "Groceries",
            "category": "Food",
            "amount": 1500,
        },
        {
            "date": "2026-09-03",
            "description": "Bus",
            "category": "Transport",
            "amount": 80,
        },
        {
            "date": "2026-09-04",
            "description": "Electricity",
            "category": "Bills",
            "amount": 2200,
        },
        {
            "date": "2026-09-05",
            "description": "Invalid record",
            "category": "Other",
            "amount": "not-a-number",
        },
    ]

    transactions = parse_transactions(records)
    analyzer = ExpenseAnalyzer(transactions)

    # Minimum-amount filtering
    minimum_amount = 500
    filtered_transactions = analyzer.filter_by_minimum_amount(
        minimum_amount
    )

    print(f"Transactions >= {minimum_amount:.2f}")
    print("-" * 60)

    for transaction in filtered_transactions:
        print(
            f"{transaction.date} | "
            f"{transaction.description} | "
            f"{transaction.category} | "
            f"{transaction.amount:.2f}"
        )

    print("\nTotal expenses:")
    print(f"{analyzer.total_expenses(minimum_amount):.2f}")

    print("\nCategory totals:")
    for category, total in analyzer.category_totals(
        minimum_amount
    ).items():
        print(f"{category}: {total:.2f}")

    print("\nLargest expense:")
    largest = analyzer.largest_expense(minimum_amount)

    if largest is not None:
        print(f"{largest.description}: {largest.amount:.2f}")
    else:
        print("No matching transactions.")


if __name__ == "__main__":
    main()