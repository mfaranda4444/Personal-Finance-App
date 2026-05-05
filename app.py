import os
from werkzeug.utils import secure_filename

import csv
from collections import defaultdict
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request

app = Flask(__name__)

EXPENSES_FILE = "expenses.csv"


MONTHLY_BUDGETS = {
    "Mortgage": 1909.56,
    "Utilities": 700.00,
    "Food": 200.00,
    "Groceries": 1400.00,
    "Gas": 100.00,
    "Misc": 1000.00
}


PAYCHECK = {
    "start_date": date(2026, 1, 2),
    "amount": 3216.11,
    "frequency_days": 14
}


RECURRING_EXPENSES = [
    {
        "name": "Mortgage",
        "day": 15,
        "category": "Mortgage",
        "expected": 1909.56,
        "min": 1909.56,
        "max": 1909.56
    },
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
    },
    {
      "name": "Spotify",
      "day": 22,
      "category": "Entertainment",
      "expected": 18.99,
      "min": 15.00,
      "max": 20.00
    },
    {
      "name": "Ring",
      "day": 9,
      "category": "Home",
      "expected": 9.99,
      "min": 9.99,
      "max": 9.99
    },
    {
      "name": "Disney Plus",
      "day": 28,
      "category": "Entertainment",
      "expected": 20.00,
      "min": 20.00,
      "max": 40.00
    },
    {
      "name": "Southwest Gas",
      "day": 10,
      "category": "Utilities",
      "expected": 50.00,
      "min": 40.00,
      "max": 70.00
    },
    {
      "name": "Groceries",
      "day": 7,
      "category": "Groceries",
      "expected": 400.00,
      "min": 300.00,
      "max": 700.00
    }
]


CATEGORY_RULES = {
    "Food": ["STARBUCKS", "DUTCH BROS", "RESTAURANT", "CAFE", "CHICK FIL-A", "SWIG", "SONIC"],
    "Gas": ["FUEL", "CHEVRON", "EXXON", "MOBIL"],
    "Groceries": ["WALMART", "TARGET", "SMITHS", "COSTCO", "TRADER JOE"],
    "Utilities": ["ELECTRIC", "WATER", "GAS", "INTERNET", "COMCAST", "T-MOBILE", "COX"],
    "Income": ["PAYROLL", "DIRECT DEPOSIT", "SALARY"]
}

TRANSFER_KEYWORDS = [
    "APPLE PAY",
    "APPLE CASH",
    "VENMO",
    "ZELLE",
    "TRANSFER"
]

def is_transfer(description):
    description = description.upper()
    return any(keyword in description for keyword in TRANSFER_KEYWORDS)


def format_money(amount):
    return f"${amount:,.2f}"


def categorize_transaction(description):
    description = description.upper()

    if is_transfer(description):
        return "Transfer"

    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in description for keyword in keywords):
            return category

    return "Uncategorized"


def load_existing_transactions():
    existing = set()

    try:
        with open(EXPENSES_FILE, "r", newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                existing.add(tuple(row))
    except FileNotFoundError:
        pass

    return existing


def get_transactions():
    transactions = []

    try:
        with open(EXPENSES_FILE, "r", newline="") as file:
            reader = csv.reader(file)

            for row in reader:
                if len(row) != 5:
                    continue

                date_str, description, category, txn_type, amount = row

                try:
                    amount = float(amount)
                except ValueError:
                    continue

                transactions.append({
                    "date": date_str,
                    "description": description,
                    "category": category,
                    "type": txn_type,
                    "amount": amount
                })

    except FileNotFoundError:
        pass

    return transactions


def import_bank_csv_file(filename):
    existing = load_existing_transactions()

    imported = 0
    skipped = 0

    with open(filename, "r", newline="", encoding="utf-8-sig") as bank_file, \
         open(EXPENSES_FILE, "a", newline="") as expenses_file:

        reader = csv.DictReader(bank_file)
        writer = csv.writer(expenses_file)

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

    return imported, skipped


def get_dashboard_totals():
    income = 0.0
    expenses = 0.0

    for tx in get_transactions():
        if is_transfer(tx["description"]):
            continue  # 🚫 ignore transfers completely

        if tx["type"] == "Credit":
            income += tx["amount"]
        else:
            expenses += tx["amount"]

    return {
        "income": income,
        "expenses": expenses,
        "net": income - expenses
    }

def resolve_date_range(range_name):
    today = date.today()

    if range_name == "last_month":
        first_this_month = date(today.year, today.month, 1)
        last_month_end = first_this_month - timedelta(days=1)
        start = date(last_month_end.year, last_month_end.month, 1)
        end = first_this_month

    elif range_name == "last_30":
        start = today - timedelta(days=30)
        end = today + timedelta(days=1)

    elif range_name == "last_90":
        start = today - timedelta(days=90)
        end = today + timedelta(days=1)

    elif range_name == "ytd":
        start = date(today.year, 1, 1)
        end = today + timedelta(days=1)

    else:  # "this_month" or default
        start = date(today.year, today.month, 1)
        end = (
            date(today.year + 1, 1, 1)
            if today.month == 12
            else date(today.year, today.month + 1, 1)
        )

    return start, end

def get_monthly_summary():
    monthly = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})

    for tx in get_transactions():
        if is_transfer(tx["description"]):
            continue  # 🚫 skip transfers

        try:
            month = datetime.strptime(tx["date"], "%m/%d/%Y").strftime("%Y-%m")
        except ValueError:
            continue

        if tx["type"] == "Credit":
            monthly[month]["income"] += tx["amount"]
        else:
            monthly[month]["expenses"] += tx["amount"]

    rows = []

    for month in sorted(monthly):
        income = monthly[month]["income"]
        expenses = monthly[month]["expenses"]

        rows.append({
            "month": month,
            "income": income,
            "expenses": expenses,
            "net": income - expenses
        })

    return rows


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


def generate_recurring_expenses(start, end):
    expenses = []
    current = date(start.year, start.month, 1)

    while current <= end:
        for bill in RECURRING_EXPENSES:
            try:
                bill_date = date(current.year, current.month, bill["day"])
            except ValueError:
                continue

            if start <= bill_date <= end:
                expenses.append({
                    "date": bill_date,
                    "description": bill["name"],
                    "category": bill["category"],
                    "expected": bill["expected"],
                    "min": bill["min"],
                    "max": bill["max"]
                })

        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    return expenses


def get_budget_vs_forecast():
    today = date.today()
    start = date(today.year, today.month, 1)

    if today.month == 12:
        end = date(today.year + 1, 1, 1)
    else:
        end = date(today.year, today.month + 1, 1)

    recurring_bills = generate_recurring_expenses(start, end)
    forecast_totals = defaultdict(float)

    for bill in recurring_bills:
        forecast_totals[bill["category"]] += bill["expected"]

    rows = []

    for category, budget in MONTHLY_BUDGETS.items():
        forecast = forecast_totals.get(category, 0.0)
        remaining = budget - forecast

        rows.append({
            "category": category,
            "budget": budget,
            "forecast": forecast,
            "remaining": remaining,
            "status": "OVER" if remaining < 0 else "OK"
        })

    return rows


def get_cash_flow_forecast(days=90, starting_balance=0.0):
    start = date.today()
    end = start + timedelta(days=days)

    events = []

    for paycheck in generate_paychecks(start, end):
        events.append({
            "date": paycheck["date"],
            "description": paycheck["description"],
            "amount": paycheck["amount"]
        })

    for bill in generate_recurring_expenses(start, end):
        events.append({
            "date": bill["date"],
            "description": bill["description"],
            "amount": -bill["expected"]
        })

    events.sort(key=lambda event: event["date"])

    balance = starting_balance
    rows = []

    for event in events:
        balance += event["amount"]

        rows.append({
            "date": event["date"].strftime("%Y-%m-%d"),
            "description": event["description"],
            "amount": event["amount"],
            "balance": balance
        })

    return rows


@app.template_filter("money")
def money_filter(amount):
    return format_money(amount)


@app.route("/")
def dashboard():
    totals = get_dashboard_totals()
    return render_template("dashboard.html", totals=totals)


UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/import", methods=["GET", "POST"])
def import_csv():
    message = None
    error = None

    if request.method == "POST":
        if "file" not in request.files:
            error = "No file provided."
        else:
            file = request.files["file"]

            if file.filename == "":
                error = "No file selected."
            elif not allowed_file(file.filename):
                error = "Only CSV files are allowed."
            else:
                filename = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(path)

                imported, skipped = import_bank_csv_file(path)
                message = f"Imported {imported} transactions. Skipped {skipped} duplicates."

    return render_template("import.html", message=message, error=error)



@app.route("/transactions")
def transactions():
    range_name = request.args.get("range", "this_month")
    search_query = request.args.get("q", "").strip().lower()

    start_date, end_date = resolve_date_range(range_name)

    rows = []
    transaction_count = 0
    total_amount = 0.0

    for tx in get_transactions():
        try:
            tx_date = datetime.strptime(tx["date"], "%m/%d/%Y").date()
        except ValueError:
            continue

        if not (start_date <= tx_date < end_date):
            continue

        if search_query:
            haystack = f"{tx['description']} {tx['category']}".lower()
            if search_query not in haystack:
                continue

        rows.append(tx)
        transaction_count += 1

        # Only count debits toward "spending"
        if tx["type"] == "Debit":
            total_amount += tx["amount"]

    return render_template(
        "transactions.html",
        transactions=rows,
        active_range=range_name,
        search_query=search_query,
        transaction_count=transaction_count,
        total_amount=total_amount
    )

@app.route("/monthly-summary")
def monthly_summary():
    rows = get_monthly_summary()
    return render_template("monthly_summary.html", rows=rows)


@app.route("/budget-forecast")
def budget_forecast():
    rows = get_budget_vs_forecast()
    return render_template("budget_forecast.html", rows=rows)


@app.route("/cash-flow")
def cash_flow():
    rows = get_cash_flow_forecast()
    return render_template("cash_flow.html", rows=rows)


if __name__ == "__main__":
    app.run(debug=True)

