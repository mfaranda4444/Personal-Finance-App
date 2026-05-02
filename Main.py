import csv

CATEGORY_RULES = {
    "Food": [
        "STARBUCKS", "DUTCH BROS", "RESTAURANT", "CAFE", "CHICK FIL-A", "SWIG"
    ],
    "Gas": [
        "FUEL", "CHEVRON", "EXXON", "MOBIL"
    ],
    "Groceries": [
        "WALMART", "TARGET", "SMITHS", "COSTCO", "TRADER JOE"
    ],
    "Utilities": [
        "ELECTRIC", "WATER", "GAS BILL", "INTERNET", "COMCAST"
    ],
    "Income": [
        "PAYROLL", "DIRECT DEPOSIT", "SALARY"
    ]
}

EXPENSES_FILE = "expenses.csv"


def categorize_transaction(description):
    description = description.upper()

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in description:
                return category

    return "Uncategorized"


def import_bank_csv(filename):
    with open(filename, "r", newline="", encoding="utf-8-sig") as bank_file, \
         open(EXPENSES_FILE, "a", newline="") as expenses_file:

        reader = csv.DictReader(bank_file)
        writer = csv.writer(expenses_file)

        imported = 0

        for row in reader:
            date = row.get("Date")
            description = row.get("Description", "")
            amount = row.get("Amount")

            if not date or not amount:
                continue

            category = categorize_transaction(description)
            writer.writerow([date, description, category, amount])
            imported += 1

    print(f"Imported {imported} transactions.")


def show_expenses():
    try:
        with open(EXPENSES_FILE, "r") as file:
            reader = csv.reader(file)
            total = 0

            print("\nTransactions:")
            for row in reader:
                date, description, category, amount = row
                amount = float(amount)
                print(f"{date} | {category:<12} | {description} | ${amount}")
                total += amount

            print(f"\nNet total: ${total}")

    except FileNotFoundError:
        print("No expenses found yet.")


while True:
    print("\n1. Import bank CSV")
    print("2. Show transactions")
    print("3. Exit")

    choice = input("Choose an option: ").strip()

    if choice == "1":
        filename = input("Enter bank CSV filename: ").strip()
        import_bank_csv(filename)
    elif choice == "2":
        show_expenses()
    elif choice == "3":
        break
    else:
        print("Invalid choice.")