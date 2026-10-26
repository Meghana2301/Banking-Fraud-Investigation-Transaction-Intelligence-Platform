
"""Compare amount-based fraud alert thresholds on PaySim synthetic data.

Run: python scripts/paysim_threshold_analysis.py

These are exploratory rules, not production fraud detection models.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    ROOT / "data" / "external"
    / "PS_20174392719_1491204439457_log.csv"
)

OUTPUT_PATH = ROOT / "data" / "paysim_threshold_results.csv"

THRESHOLDS = [10000, 50000, 100000, 250000, 500000, 1000000]
TRANSACTION_TYPES = ["TRANSFER", "CASH_OUT"]


def calculate_metrics(tp, fp, tn, fn):
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    fpr = fp / (fp + tn) if fp + tn else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )

    return {
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "false_positive_rate": round(fpr, 6),
        "f1_score": round(f1, 6),
        "investigation_queue": tp + fp,
    }


def main():
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Missing dataset: {DATA_PATH}")

    # Each candidate rule is evaluated against all transactions.
    counts = {
        (transaction_type, threshold): [0, 0, 0, 0]
        for transaction_type in TRANSACTION_TYPES
        for threshold in THRESHOLDS
    }

    total = 0

    with DATA_PATH.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            total += 1
            actual = int(row["isFraud"])
            transaction_type = row["type"]
            amount = float(row["amount"])

            for rule_type in TRANSACTION_TYPES:
                for threshold in THRESHOLDS:
                    predicted = int(
                        transaction_type == rule_type
                        and amount >= threshold
                    )

                    metrics = counts[(rule_type, threshold)]

                    if actual == 1 and predicted == 1:
                        metrics[0] += 1
                    elif actual == 0 and predicted == 1:
                        metrics[1] += 1
                    elif actual == 0 and predicted == 0:
                        metrics[2] += 1
                    else:
                        metrics[3] += 1

    results = []

    for (rule_type, threshold), (tp, fp, tn, fn) in counts.items():
        result = {
            "rule": f"{rule_type} amount >= {threshold}",
            "transaction_type": rule_type,
            "threshold": threshold,
            "total_transactions": total,
            **calculate_metrics(tp, fp, tn, fn),
        }
        results.append(result)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("\n========== PAYSIM THRESHOLD ANALYSIS ==========")
    print(f"Total transactions evaluated: {total:,}")

    for result in results:
        print(f"\n{result['rule']}")
        print(f"  Precision: {result['precision']:.2%}")
        print(f"  Recall: {result['recall']:.2%}")
        print(f"  False positives: {result['false_positives']:,}")
        print(f"  Investigation queue: {result['investigation_queue']:,}")

    print(f"\nResults saved to: {OUTPUT_PATH}")
    print("Note: All fraud labels are simulated.")


if __name__ == "__main__":
    main()
