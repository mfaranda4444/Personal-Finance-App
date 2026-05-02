import csv

FILENAME = "expenses.csv"


def add_expense():
    amount = input("Enter amount: ")
    category = input("Enter category: ")

    with open(FILENAME, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([amount, category])

    print("Expense saved!")


def show_expenses():
    try:
        with open(FILENAME, "r") as file:
            reader = csv.reader(file)
            total = 0

            print("\nYour Expenses:")
            for row in reader:
                if len(row) == 0:
                    continue
                amount = float(row[0])
                category = row[1]
                print(f"{category}: ${amount}")
                total += amount

            print(f"\nTotal spending: ${total}")

    except FileNotFoundError:
        print("No expenses found yet.")


while True:
    print("\n1. Add Expense")
    print("2. Show Expenses")
    print("3. Exit")

    choice = input("Choose an option: ")

    if choice == "1":
        add_expense()
    elif choice == "2":
        show_expenses()
    elif choice == "3":
        print("Goodbye!")
        break
    else:
        print("Invalid choice")