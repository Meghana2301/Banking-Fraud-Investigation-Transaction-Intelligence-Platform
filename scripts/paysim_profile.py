
"""Profile the public PaySim synthetic transaction dataset.

Run: python scripts/paysim_profile.py
Uses streaming CSV processing to avoid loading the full dataset into memory.
"""

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "external" / "PS_20174392719_1491204439457_log.csv"


def main():
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    total_transactions = 0
    fraud_transactions = 0
    flagged_transactions = 0
    transaction_types = Counter()
    fraud_by_type = Counter()
    amount_by_type = defaultdict(float)
    missing_values = Counter()

    with DATA_PATH.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            total_transactions += 1

            transaction_type = row["type"]
            amount = float(row["amount"])
            is_fraud = int(row["isFraud"])
            is_flagged = int(row["isFlaggedFraud"])

            transaction_types[transaction_type] += 1
            amount_by_type[transaction_type] += amount

            if is_fraud == 1:
                fraud_transactions += 1
                fraud_by_type[transaction_type] += 1

            if is_flagged == 1:
                flagged_transactions += 1

            for column, value in row.items():
                if value is None or not value.strip():
                    missing_values[column] += 1

    print("\n========== PAYSIM DATA PROFILE ==========")
    print(f"Total transactions: {total_transactions:,}")
    print(f"Fraud-labeled transactions: {fraud_transactions:,}")
    print(f"Existing rule flags: {flagged_transactions:,}")

    fraud_rate = (
        fraud_transactions / total_transactions * 100
        if total_transactions else 0
    )
    print(f"Fraud label rate: {fraud_rate:.4f}%")

    print("\nTRANSACTION TYPE ANALYSIS")
    print("-" * 65)

    for transaction_type, count in transaction_types.most_common():
        fraud_count = fraud_by_type[transaction_type]
        type_fraud_rate = fraud_count / count * 100 if count else 0

        print(
            f"{transaction_type:12} "
            f"Transactions: {count:>10,} | "
            f"Fraud: {fraud_count:>6,} | "
            f"Rate: {type_fraud_rate:.4f}%"
        )

    print("\nTOTAL TRANSACTION AMOUNT BY TYPE")
    print("-" * 45)

    for transaction_type, amount in sorted(amount_by_type.items()):
        print(f"{transaction_type:12} {amount:,.2f}")

    print("\nMISSING VALUES")
    print("-" * 45)

    if missing_values:
        for column, count in missing_values.items():
            print(f"{column}: {count:,}")
    else:
        print("No blank or missing values detected.")

    print("\nProfiling completed successfully.")


if __name__ == "__main__":
    main()
