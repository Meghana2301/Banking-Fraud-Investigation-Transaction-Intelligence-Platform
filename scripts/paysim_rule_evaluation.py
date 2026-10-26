
"""Evaluate PaySim's existing fraud flag against synthetic fraud labels.

Run: python scripts/paysim_rule_evaluation.py

This analysis uses simulated labels, not verified real-world fraud.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = (
    ROOT
    / "data"
    / "external"
    / "PS_20174392719_1491204439457_log.csv"
)


def main():
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    tp = fp = tn = fn = 0

    with DATA_PATH.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            actual = int(row["isFraud"])
            predicted = int(row["isFlaggedFraud"])

            if actual == 1 and predicted == 1:
                tp += 1
            elif actual == 0 and predicted == 1:
                fp += 1
            elif actual == 0 and predicted == 0:
                tn += 1
            elif actual == 1 and predicted == 0:
                fn += 1

    total = tp + fp + tn + fn

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    fpr = fp / (fp + tn) if (fp + tn) else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) else 0
    )

    print("\n========== PAYSIM RULE EVALUATION ==========")
    print(f"Total transactions: {total:,}")

    print("\nCONFUSION MATRIX")
    print("-" * 40)
    print(f"True Positives:  {tp:,}")
    print(f"False Positives: {fp:,}")
    print(f"True Negatives:  {tn:,}")
    print(f"False Negatives: {fn:,}")

    print("\nDETECTION PERFORMANCE")
    print("-" * 40)
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"False Positive Rate: {fpr:.4%}")
    print(f"F1 Score: {f1:.2%}")
    print(f"Investigation Queue: {tp + fp:,}")
    print(f"Missed Fraud-Labeled Transactions: {fn:,}")

    print("\nNote: Results reflect synthetic PaySim labels.")
    print("They do not establish real-world detection performance.")


if __name__ == "__main__":
    main()
