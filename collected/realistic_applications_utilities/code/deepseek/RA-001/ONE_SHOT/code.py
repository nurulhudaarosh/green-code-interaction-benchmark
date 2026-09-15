import csv
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import os

class ExpenseAnalyzer:
    def __init__(self, filename='expenses.csv'):
        self.filename = filename
        self.expenses = []
        self.categories = ['Food', 'Transport', 'Entertainment', 'Bills', 'Shopping', 'Other']
        self._initialize_file()
        self.load_expenses()
    
    def _initialize_file(self):
        """Initialize CSV file if it doesn't exist"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Date', 'Category', 'Description', 'Amount'])
    
    # Requirement 1: Add expenses with validation
    def add_expense(self, date, category, description, amount):
        """Add a new expense with validation"""
        try:
            # Validate date format
            datetime.strptime(date, '%Y-%m-%d')
            
            # Validate category
            if category not in self.categories:
                print(f"Error: Category must be one of {self.categories}")
                return False
            
            # Validate amount
            amount = float(amount)
            if amount <= 0:
                print("Error: Amount must be positive")
                return False
            
            # Add to CSV file
            with open(self.filename, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([date, category, description, amount])
            
            # Add to memory
            self.expenses.append({
                'date': date,
                'category': category,
                'description': description,
                'amount': amount
            })
            
            print(f"✓ Expense added: {description} - ${amount:.2f}")
            return True
            
        except ValueError as e:
            print(f"Error: Invalid input - {e}")
            return False
    
    # Requirement 2: Load and display expenses
    def load_expenses(self):
        """Load expenses from CSV file"""
        self.expenses = []
        try:
            with open(self.filename, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    row['amount'] = float(row['amount'])
                    self.expenses.append(row)
        except FileNotFoundError:
            print("No existing expense file found. Starting fresh.")
    
    def display_expenses(self, limit=None):
        """Display all expenses or limited number"""
        if not self.expenses:
            print("No expenses recorded.")
            return
        
        print("\n" + "="*70)
        print(f"{'Date':<12} {'Category':<15} {'Description':<25} {'Amount':<10}")
        print("-"*70)
        
        expenses_to_show = self.expenses[-limit:] if limit else self.expenses
        
        for exp in expenses_to_show:
            print(f"{exp['date']:<12} {exp['category']:<15} {exp['description']:<25} ${exp['amount']:<9.2f}")
        print("="*70)
    
    # Requirement 3: Calculate statistics
    def calculate_statistics(self):
        """Calculate various expense statistics"""
        if not self.expenses:
            print("No expenses to analyze.")
            return {}
        
        total = sum(exp['amount'] for exp in self.expenses)
        avg = total / len(self.expenses)
        
        # Category breakdown
        category_totals = defaultdict(float)
        category_counts = defaultdict(int)
        
        for exp in self.expenses:
            category_totals[exp['category']] += exp['amount']
            category_counts[exp['category']] += 1
        
        # Monthly breakdown
        monthly_totals = defaultdict(float)
        for exp in self.expenses:
            month = exp['date'][:7]  # YYYY-MM
            monthly_totals[month] += exp['amount']
        
        stats = {
            'total': total,
            'average': avg,
            'count': len(self.expenses),
            'category_totals': dict(category_totals),
            'category_counts': dict(category_counts),
            'monthly_totals': dict(monthly_totals),
            'max_expense': max(self.expenses, key=lambda x: x['amount']),
            'min_expense': min(self.expenses, key=lambda x: x['amount'])
        }
        
        return stats
    
    def print_statistics(self):
        """Print formatted statistics"""
        stats = self.calculate_statistics()
        if not stats:
            return
        
        print("\n" + "="*50)
        print("EXPENSE STATISTICS")
        print("="*50)
        print(f"Total Expenses: ${stats['total']:.2f}")
        print(f"Number of Transactions: {stats['count']}")
        print(f"Average Expense: ${stats['average']:.2f}")
        print(f"Largest Expense: ${stats['max_expense']['amount']:.2f} ({stats['max_expense']['description']})")
        print(f"Smallest Expense: ${stats['min_expense']['amount']:.2f} ({stats['min_expense']['description']})")
        
        print("\nCategory Breakdown:")
        print("-"*40)
        for category, total in sorted(stats['category_totals'].items(), key=lambda x: x[1], reverse=True):
            percentage = (total / stats['total']) * 100
            count = stats['category_counts'][category]
            print(f"{category:<15} ${total:>8.2f} ({percentage:>5.1f}%) - {count} transactions")
        
        print("\nMonthly Breakdown:")
        print("-"*40)
        for month, total in sorted(stats['monthly_totals'].items()):
            print(f"{month}: ${total:.2f}")
    
    # Requirement 4: Filter expenses
    def filter_expenses(self, category=None, start_date=None, end_date=None, min_amount=None, max_amount=None):
        """Filter expenses by various criteria"""
        filtered = self.expenses.copy()
        
        if category:
            filtered = [e for e in filtered if e['category'] == category]
        
        if start_date:
            filtered = [e for e in filtered if e['date'] >= start_date]
        
        if end_date:
            filtered = [e for e in filtered if e['date'] <= end_date]
        
        if min_amount is not None:
            filtered = [e for e in filtered if e['amount'] >= min_amount]
        
        if max_amount is not None:
            filtered = [e for e in filtered if e['amount'] <= max_amount]
        
        return filtered
    
    def search_expenses(self, keyword):
        """Search expenses by keyword in description"""
        keyword = keyword.lower()
        results = [e for e in self.expenses if keyword in e['description'].lower()]
        return results
    
    # Requirement 5: Visualization
    def visualize_expenses(self, chart_type='category'):
        """Create visualizations of expense data"""
        if not self.expenses:
            print("No expenses to visualize.")
            return
        
        stats = self.calculate_statistics()
        
        if chart_type == 'category':
            # Pie chart of expenses by category
            categories = list(stats['category_totals'].keys())
            amounts = list(stats['category_totals'].values())
            
            plt.figure(figsize=(10, 6))
            plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
            plt.title('Expenses by Category')
            plt.axis('equal')
            plt.show()
            
        elif chart_type == 'monthly':
            # Bar chart of monthly expenses
            months = list(stats['monthly_totals'].keys())
            amounts = list(stats['monthly_totals'].values())
            
            plt.figure(figsize=(10, 6))
            plt.bar(months, amounts, color='steelblue')
            plt.xlabel('Month')
            plt.ylabel('Amount ($)')
            plt.title('Monthly Expenses')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
            
        elif chart_type == 'trend':
            # Line chart of expense trend over time
            dates = [datetime.strptime(e['date'], '%Y-%m-%d') for e in self.expenses]
            amounts = [e['amount'] for e in self.expenses]
            
            # Sort by date
            sorted_data = sorted(zip(dates, amounts))
            dates, amounts = zip(*sorted_data)
            
            plt.figure(figsize=(12, 6))
            plt.plot(dates, amounts, marker='o', linestyle='-', color='green', alpha=0.7)
            plt.xlabel('Date')
            plt.ylabel('Amount ($)')
            plt.title('Expense Trend Over Time')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
    
    def export_report(self, filename='expense_report.txt'):
        """Export a text report of expenses"""
        stats = self.calculate_statistics()
        
        with open(filename, 'w') as file:
            file.write("="*60 + "\n")
            file.write("EXPENSE ANALYZER REPORT\n")
            file.write("="*60 + "\n\n")
            
            file.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            file.write("SUMMARY\n")
            file.write("-"*40 + "\n")
            file.write(f"Total Expenses: ${stats['total']:.2f}\n")
            file.write(f"Number of Transactions: {stats['count']}\n")
            file.write(f"Average Expense: ${stats['average']:.2f}\n\n")
            
            # Category breakdown
            file.write("CATEGORY BREAKDOWN\n")
            file.write("-"*40 + "\n")
            for category, total in sorted(stats['category_totals'].items(), key=lambda x: x[1], reverse=True):
                percentage = (total / stats['total']) * 100
                file.write(f"{category:<15} ${total:>8.2f} ({percentage:>5.1f}%)\n")
            
            # All expenses
            file.write("\nALL EXPENSES\n")
            file.write("-"*40 + "\n")
            for exp in self.expenses:
                file.write(f"{exp['date']} | {exp['category']:<15} | {exp['description']:<25} | ${exp['amount']:.2f}\n")
        
        print(f"✓ Report exported to {filename}")


def main():
    """Main program with interactive menu"""
    analyzer = ExpenseAnalyzer()
    
    # Add some sample data if file is empty
    if not analyzer.expenses:
        print("Adding sample data...")
        sample_expenses = [
            ('2024-01-15', 'Food', 'Groceries', 85.50),
            ('2024-01-16', 'Transport', 'Gas', 45.00),
            ('2024-01-17', 'Entertainment', 'Movie tickets', 25.00),
            ('2024-01-18', 'Bills', 'Electricity', 120.00),
            ('2024-01-20', 'Food', 'Restaurant', 65.00),
            ('2024-02-01', 'Shopping', 'Clothes', 150.00),
            ('2024-02-05', 'Transport', 'Bus pass', 50.00),
            ('2024-02-10', 'Food', 'Groceries', 95.00),
            ('2024-02-14', 'Entertainment', 'Concert', 80.00),
            ('2024-02-15', 'Bills', 'Internet', 60.00),
        ]
        for date, cat, desc, amt in sample_expenses:
            analyzer.add_expense(date, cat, desc, amt)
    
    while True:
        print("\n" + "="*50)
        print("EXPENSE ANALYZER")
        print("="*50)
        print("1. Add Expense")
        print("2. View All Expenses")
        print("3. View Statistics")
        print("4. Filter Expenses")
        print("5. Search Expenses")
        print("6. Visualize Data")
        print("7. Export Report")
        print("8. Exit")
        print("-"*50)
        
        choice = input("Enter your choice (1-8): ").strip()
        
        if choice == '1':
            print("\n--- Add New Expense ---")
            date = input("Date (YYYY-MM-DD): ").strip()
            print(f"Categories: {', '.join(analyzer.categories)}")
            category = input("Category: ").strip()
            description = input("Description: ").strip()
            amount = input("Amount: ").strip()
            analyzer.add_expense(date, category, description, amount)
        
        elif choice == '2':
            limit = input("Show last N expenses (press Enter for all): ").strip()
            limit = int(limit) if limit else None
            analyzer.display_expenses(limit)
        
        elif choice == '3':
            analyzer.print_statistics()
        
        elif choice == '4':
            print("\n--- Filter Expenses ---")
            print("Leave blank to skip filter")
            category = input(f"Category ({', '.join(analyzer.categories)}): ").strip() or None
            start_date = input("Start date (YYYY-MM-DD): ").strip() or None
            end_date = input("End date (YYYY-MM-DD): ").strip() or None
            min_amount = input("Minimum amount: ").strip()
            max_amount = input("Maximum amount: ").strip()
            
            min_amount = float(min_amount) if min_amount else None
            max_amount = float(max_amount) if max_amount else None
            
            filtered = analyzer.filter_expenses(category, start_date, end_date, min_amount, max_amount)
            
            if filtered:
                print(f"\nFound {len(filtered)} expenses:")
                for exp in filtered:
                    print(f"{exp['date']} | {exp['category']:<15} | {exp['description']:<25} | ${exp['amount']:.2f}")
            else:
                print("No expenses match the filter criteria.")
        
        elif choice == '5':
            keyword = input("Enter search keyword: ").strip()
            results = analyzer.search_expenses(keyword)
            
            if results:
                print(f"\nFound {len(results)} matching expenses:")
                for exp in results:
                    print(f"{exp['date']} | {exp['category']:<15} | {exp['description']:<25} | ${exp['amount']:.2f}")
            else:
                print("No matching expenses found.")
        
        elif choice == '6':
            print("\n--- Visualization Options ---")
            print("1. Category Pie Chart")
            print("2. Monthly Bar Chart")
            print("3. Expense Trend Line")
            chart_choice = input("Choose chart type (1-3): ").strip()
            
            if chart_choice == '1':
                analyzer.visualize_expenses('category')
            elif chart_choice == '2':
                analyzer.visualize_expenses('monthly')
            elif chart_choice == '3':
                analyzer.visualize_expenses('trend')
            else:
                print("Invalid choice.")
        
        elif choice == '7':
            filename = input("Enter filename (default: expense_report.txt): ").strip()
            filename = filename if filename else 'expense_report.txt'
            analyzer.export_report(filename)
        
        elif choice == '8':
            print("\nThank you for using Expense Analyzer. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()