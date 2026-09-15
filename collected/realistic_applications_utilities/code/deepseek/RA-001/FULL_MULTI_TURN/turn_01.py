import csv
from collections import defaultdict
from datetime import datetime

class ExpenseAnalyzer:
    def __init__(self):
        self.expenses = []
    
    def add_expense(self, date, category, amount, description=""):
        """Add a single expense entry"""
        try:
            expense_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {date}. Use YYYY-MM-DD")
        
        self.expenses.append({
            "date": expense_date,
            "category": category,
            "amount": float(amount),
            "description": description
        })
    
    def load_from_csv(self, filepath):
        """Load expenses from a CSV file with columns: date,category,amount,description"""
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.add_expense(
                    row['date'],
                    row['category'],
                    row['amount'],
                    row.get('description', '')
                )
    
    def total(self):
        """Total of all expenses"""
        return sum(e["amount"] for e in self.expenses)
    
    def by_category(self):
        """Sum of expenses grouped by category"""
        totals = defaultdict(float)
        for e in self.expenses:
            totals[e["category"]] += e["amount"]
        return dict(sorted(totals.items(), key=lambda x: -x[1]))
    
    def by_month(self):
        """Sum of expenses grouped by YYYY-MM"""
        totals = defaultdict(float)
        for e in self.expenses:
            key = e["date"].strftime("%Y-%m")
            totals[key] += e["amount"]
        return dict(sorted(totals.items()))
    
    def top_expenses(self, n=5):
        """Return the n largest expenses"""
        return sorted(self.expenses, key=lambda x: -x["amount"])[:n]
    
    def summary(self):
        """Print a full summary report"""
        if not self.expenses:
            print("No expenses recorded.")
            return
        
        print("=" * 50)
        print("EXPENSE ANALYZER SUMMARY")
        print("=" * 50)
        print(f"Total expenses: {len(self.expenses)}")
        print(f"Total amount:   ${self.total():,.2f}")
        if self.expenses:
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


if __name__ == "__main__":
    analyzer = ExpenseAnalyzer()
    
    # Demo data
    demo = [
        ("2024-01-05", "Food",          45.20, "Groceries"),
        ("2024-01-12", "Transport",     30.00, "Gas"),
        ("2024-01-20", "Food",          62.75, "Restaurant"),
        ("2024-02-03", "Utilities",    120.00, "Electric bill"),
        ("2024-02-14", "Entertainment", 85.50, "Concert tickets"),
        ("2024-02-22", "Food",          38.90, "Groceries"),
        ("2024-03-01", "Transport",     45.00, "Train pass"),
        ("2024-03-15", "Utilities",     95.30, "Internet"),
    ]
    
    for date, cat, amt, desc in demo:
        analyzer.add_expense(date, cat, amt, desc)
    
    analyzer.summary()