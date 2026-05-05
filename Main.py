import csv
from collections import defaultdict
from datetime import datetime, date, timedelta

MONTHLY_BUDGETS = {
    "Mortgage": 1909.56,
    "Utilities": 700.00,
    "Food": 200.00,
    "Groceries": 1400.00,
    "Gas": 100.00,
    "Misc": 1000.00
}
# =========================
# PAYCHECK CONFIG
# =========================

PAYCHECK = {
    "start_date": date(2026, 1, 2),  # first known paycheck
    "amount": 3216.11,
    "frequency_days": 14
}

def generate_paychecks(start, end):
    paychecks = []
    current = PAYCHECK["start_date"]

    while current <= end:
        if current >= start:
            paychecks.append({
                "date": current,
                "description": "Paycheck",
                "amount": PAYCHECK["amount"]
            })
        current += timedelta(days=PAYCHECK["frequency_days"])

    return paychecks
# =========================
# RECURRING EXPENSES
# (fixed bills just have same min/max/expected)
# =========================

RECURRING_EXPENSES = [
    # =========================
    # Housing
    # =========================
    {
        "name": "Mortgage",
        "day": 15,
        "category": "Mortgage",
        "expected": 1909.56,
        "min": 1909.56,
        "max": 1909.56
    },

    # =========================
    # Utilities
    # =========================
    {
        "name": "T-Mobile",
        "day": 9,
        "category": "Utilities",
        "expected": 165.00,
        "min": 165.00,
        "max": 165.00
    },
    {
        "name": "Cox Communications",
        "day": 24,
        "category": "Utilities",
        "expected": 90.00,
        "min": 90.00,
        "max": 90.00
    },
    {
        "name": "NV Energy",
        "day": 29,
        "category": "Utilities",
        "expected": 250.00,
        "min": 200.00,
        "max": 400.00
    },
    {
        "name": "Southwest Gas",
        "day": 8,
        "category": "Utilities",
        "expected": 45.00,
        "min": 40.00,
        "max": 80.00
    },
    {
        "name": "Las Vegas Valley Water",
        "day": 15,
        "category": "Utilities",
        "expected": 50.00,
        "min": 40.00,
        "max": 70.00
    }
]

def forecast_expenses_by_category(month, year):
    start = date(year, month, 1)
    end = (
        date(year + 1, 1, 1)
        if month == 12
        else date(year, month + 1, 1)
    )

    expenses = generate_recurring_expenses(start, end)
    totals = defaultdict(float)

    for expense in expenses:
        category = expense["category"]
        expected = expense["expected"]

        totals[category] += expected

    return totals

def show_budget_vs_forecast(month=None, year=None):
    today = date.today()
    month = month or today.month
    year = year or today.year

    forecast_totals = forecast_expenses_by_category(month, year)

    print(f"\nBudget vs Forecast — {year}-{month:02d}\n")

    for category, budget in MONTHLY_BUDGETS.items():
        forecast = forecast_totals.get(category, 0.0)
        remaining = budget - forecast

        status = "OK"
        if remaining < 0:
            status = "OVER"

        print(
            f"{category:<12} | "
            f"Budget: {budget:>7.2f} | "
            f"Forecast: {forecast:>7.2f} | "
            f"Remaining: {remaining:>7.2f} | {status}"
        )

def generate_recurring_expenses(start, end):
    expenses = []
    current = date(start.year, start.month, 1)

    while current <= end:
        for bill in RECURRING_EXPENSES:
            try:
                bill_date = date(current.year, current.month, bill["day"])
            except ValueError:
                continue  # skip invalid days like Feb 30

            if start <= bill_date <= end:
                expenses.append({
                    "date": bill_date,
                    "description": bill["name"],
                    "expected": bill["expected"],
                    "min": bill["min"],
                    "max": bill["max"],
                    "category": bill["category"]
                })

        # advance month
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    return expenses

def forecast_cash_flow(days=90, starting_balance=0.0):
    start = date.today()
    end = start + timedelta(days=days)

    paychecks = generate_paychecks(start, end)
    bills = generate_recurring_expenses(start, end)

    events = []

    for p in paychecks:
        events.append({
            "date": p["date"],
            "description": p["description"],
            "amount": p["amount"]
        })

    for b in bills:
        events.append({
            "date": b["date"],
            "description": b["description"],
            "amount": -b["expected"]  # forecast uses expected
        })

    events.sort(key=lambda x: x["date"])

    balance = starting_balance

    print(f"\nForecast (next {days} days)\n")
    for e in events:
        balance += e["amount"]
        sign = "+" if e["amount"] > 0 else ""
        print(
            f"{e['date']} | "
            f"{e['description']:<20} | "
            f"{sign}{e['amount']:.2f} | "
            f"Balance: {balance:.2f}"
        )
# =========================
# CATEGORY RULES
# =========================

CATEGORY_RULES = {
    "Food": ["STARBUCKS", "DUTCH BROS", "RESTAURANT", "CAFE", "CHICK FIL-A", "SWIG"],
    "Gas": ["FUEL", "CHEVRON", "EXXON", "MOBIL"],
    "Groceries": ["WALMART", "TARGET", "SMITHS", "COSTCO", "TRADER JOE"],
    "Utilities": ["ELECTRIC", "WATER", "GAS", "INTERNET", "COMCAST"],
    "Income": ["PAYROLL", "DIRECT DEPOSIT", "SALARY"]
}

EXPENSES_FILE = "expenses.csv"

# =========================
# UTILITIES
# =========================

def categorize_transaction(description):
    description = description.upper()
    for category, keywords in CATEGORY_RULES.items():
        if any(word in description for word in keywords):
            return category
    return "Uncategorized"


def load_existing_transactions():
    existing = set()
    try:
        with open(EXPENSES_FILE, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                existing.add(tuple(row))
    except FileNotFoundError:
        pass
    return existing

# =========================
# BANK CSV IMPORT
# =========================

def import_bank_csv(filename):
    existing = load_existing_transactions()

    with open(filename, "r", newline="", encoding="utf-8-sig") as bank_file, \
         open(EXPENSES_FILE, "a", newline="") as expenses_file:

        reader = csv.DictReader(bank_file)
        writer = csv.writer(expenses_file)

        imported = skipped = 0

        for row in reader:
            date_str = row.get("Date")
            description = row.get("Description", "")
            amount = row.get("Amount")
            txn_type = row.get("Type")

            if not date_str or not amount or not txn_type:
                continue

            category = categorize_transaction(description)
            record = (date_str, description, category, txn_type, amount)

            if record in existing:
                skipped += 1
                continue

            writer.writerow(record)
            existing.add(record)
            imported += 1

    print(f"Imported: {imported}")
    print(f"Skipped duplicates: {skipped}")

# =========================
# DISPLAY FUNCTIONS
# =========================

def show_expenses():
    try:
        with open(EXPENSES_FILE, "r") as file:
            reader = csv.reader(file)

            income = expenses = 0.0
            print("\nTransactions:")

            for date_str, desc, cat, txn_type, amt in reader:
                amt = float(amt)
                direction = "IN " if txn_type == "Credit" else "OUT"
                print(f"{date_str} | {direction} | {cat:<15} | {desc} | ${amt:.2f}")
                if txn_type == "Credit":
                    income += amt
                else:
                    expenses += amt

            print("\nSummary:")
            print(f"Total Income:    ${income:.2f}")
            print(f"Total Expenses: ${expenses:.2f}")
            print(f"Net Total:      ${income - expenses:.2f}")

    except FileNotFoundError:
        print("No expenses found yet.")

def show_monthly_summary():
    monthly = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})

    try:
        with open(EXPENSES_FILE, "r") as file:
            reader = csv.reader(file)

            for date_str, _, _, txn_type, amount in reader:
                amount = float(amount)
                month = datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m")

                if txn_type == "Credit":
                    monthly[month]["income"] += amount
                else:
                    monthly[month]["expenses"] += amount

        print("\nMonthly Summary:")
        for month in sorted(monthly):
            income = monthly[month]["income"]
            expenses = monthly[month]["expenses"]
            print(f"\n{month}")
            print(f"  Income:   ${income:.2f}")
            print(f"  Expenses: ${expenses:.2f}")
            print(f"  Net:      ${income - expenses:.2f}")

    except FileNotFoundError:
        print("No expenses found yet.")

while True:
    print("\n1. Import bank CSV")
    print("2. Show transactions")
    print("3. Monthly summary")
    print("4. Exit")
    print("5. Budget vs Forecast (this month)")


    choice = input("Choose an option: ").strip()

    if choice == "1":
        filename = input("Enter bank CSV filename: ").strip()
        import_bank_csv(filename)
    elif choice == "2":
        show_expenses()
    elif choice == "3":
        show_monthly_summary()
    elif choice == "4":
        break
    elif choice == "5":
        show_budget_vs_forecast()
    else:
        print("Invalid choice.")