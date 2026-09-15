import json
import os
import sys
import matplotlib.pyplot as plt

DATA_FILE = "expense_data.json"

# ==========================================
# 5. DATA PERSISTENCE
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "expenses": {}, "budgets": {}}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"users": {}, "expenses": {}, "budgets": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ==========================================
# 1. USER AUTHENTICATION
# ==========================================
def register(data):
    print("\n--- User Registration ---")
    username = input("Enter username: ").strip().lower()
    if not username:
        print("Username cannot be empty.")
        return None
    if username in data["users"]:
        print("Username already exists!")
        return None
    password = input("Enter password: ").strip()
    
    data["users"][username] = password
    data["expenses"][username] = []
    data["budgets"][username] = {}
    save_data(data)
    print("Registration successful! You can now log in.")
    return username

def login(data):
    print("\n--- User Login ---")
    username = input("Enter username: ").strip().lower()
    password = input("Enter password: ").strip()
    
    if data["users"].get(username) == password:
        print(f"\nWelcome back, {username}!")
        return username
    else:
        print("Invalid username or password.")
        return None

# ==========================================
# 2. EXPENSE RECORDING (QUICK ADD)
# ==========================================
def add_expense(data, username):
    print("\n--- Quick Add Expense ---")
    desc = input("Description (e.g., Lunch, Bus fare): ").strip()
    try:
        amount = float(input("Amount: "))
        if amount <= 0:
            print("Amount must be greater than zero.")
            return
    except ValueError:
        print("Invalid amount entered.")
        return
    
    category = input("Category (e.g., Food, Transport, Rent, Entertainment): ").strip().title()
    if not category:
        category = "Uncategorized"
        
    expense = {
        "description": desc,
        "amount": amount,
        "category": category
    }
    
    data["expenses"][username].append(expense)
    save_data(data)
    print(f"Added expense: '{desc}' - ${amount:.2f} under [{category}]")
    
    # Check budget limits automatically upon adding expense
    check_budget_status(data, username, category)

# ==========================================
# 3. BUDGETING & LIMIT TRACKING
# ==========================================
def set_budget(data, username):
    print("\n--- Set Category Budget ---")
    category = input("Enter category name to set budget for: ").strip().title()
    try:
        limit = float(input(f"Enter monthly budget limit for {category}: "))
        if limit <= 0:
            print("Limit must be greater than zero.")
            return
    except ValueError:
        print("Invalid limit entered.")
        return

    data["budgets"][username][category] = limit
    save_data(data)
    print(f"Budget of ${limit:.2f} set for category '{category}'.")

def check_budget_status(data, username, category):
    user_budgets = data["budgets"].get(username, {})
    if category in user_budgets:
        limit = user_budgets[category]
        total_spent = sum(e["amount"] for e in data["expenses"][username] if e["category"] == category)
        
        if total_spent > limit:
            print(f"\n⚠️  [ALERT] You have EXCEEDED your budget for '{category}'!")
            print(f"    Spent: ${total_spent:.2f} | Limit: ${limit:.2f} | Over by: ${total_spent - limit:.2f}")
        elif total_spent >= limit * 0.85:
            print(f"\n⚠️  [WARNING] You have used {total_spent / limit * 100:.1f}% of your budget for '{category}'.")
            print(f"    Spent: ${total_spent:.2f} / ${limit:.2f}")

# ==========================================
# 4. DASHBOARD & VISUALIZATIONS
# ==========================================
def show_dashboard(data, username):
    user_expenses = data["expenses"].get(username, [])
    user_budgets = data["budgets"].get(username, {})
    
    print("\n==========================================")
    print(f"          EXPENSE DASHBOARD ({username.upper()})")
    print("==========================================")
    
    total_spent = sum(e["amount"] for e in user_expenses)
    print(f"Total Expenses Recorded: ${total_spent:.2f}\n")
    
    if not user_expenses:
        print("No expenses recorded yet.")
        return

    # Category totals
    cat_totals = {}
    for e in user_expenses:
        cat = e["category"]
        cat_totals[cat] = cat_totals.get(cat, 0) + e["amount"]

    print(f"{'Category':<18} | {'Spent':<10} | {'Budget':<10} | {'Status'}")
    print("-" * 55)
    for cat, spent in cat_totals.items():
        budget_str = f"${user_budgets[cat]:.2f}" if cat in user_budgets else "N/A"
        if cat in user_budgets:
            status = "OVER BUDGET!" if spent > user_budgets[cat] else "OK"
        else:
            status = "-"
        print(f"{cat:<18} | ${spent:<9.2f} | {budget_str:<10} | {status}")
    print("-" * 55)

    plot_choice = input("\nWould you like to generate a graphical visual report? (y/n): ").strip().lower()
    if plot_choice == 'y':
        generate_charts(cat_totals)

def generate_charts(cat_totals):
    categories = list(cat_totals.keys())
    amounts = list(cat_totals.values())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Pie Chart
    ax1.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
    ax1.set_title("Expense Breakdown by Category")

    # Bar Chart
    ax2.bar(categories, amounts, color='skyblue')
    ax2.set_xlabel("Categories")
    ax2.set_ylabel("Amount Spent ($)")
    ax2.set_title("Category Spending Comparison")
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.show()

# ==========================================
# MAIN APPLICATION LOOP
# ==========================================
def main():
    data = load_data()
    current_user = None

    while True:
        if not current_user:
            print("\n=== EXPENSE ANALYZER ===")
            print("1. Login")
            print("2. Register")
            print("3. Exit")
            choice = input("Select an option (1-3): ").strip()

            if choice == "1":
                current_user = login(data)
            elif choice == "2":
                current_user = register(data)
            elif choice == "3":
                print("Goodbye!")
                sys.exit()
            else:
                print("Invalid selection.")
        else:
            print(f"\n=== MAIN MENU (User: {current_user}) ===")
            print("1. Quick Add Expense")
            print("2. Set Category Budget")
            print("3. View Dashboard & Visualizations")
            print("4. Logout")
            choice = input("Select an option (1-4): ").strip()

            if choice == "1":
                add_expense(data, current_user)
            elif choice == "2":
                set_budget(data, current_user)
            elif choice == "3":
                show_dashboard(data, current_user)
            elif choice == "4":
                print(f"Logged out from {current_user}.")
                current_user = None
            else:
                print("Invalid selection.")

if __name__ == "__main__":
    main()