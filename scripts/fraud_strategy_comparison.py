
"""Compare fraud alerting strategies using synthetic transaction labels.

Run: python scripts/fraud_strategy_comparison.py
Results demonstrate analytical methods, not real-world fraud performance.
"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "banking.db"
OUTPUT_PATH = ROOT / "data" / "fraud_strategy_comparison.csv"


def calculate_metrics(records, strategy):
    tp = fp = tn = fn = 0

    for actual, predicted in records:
        if actual == 1 and predicted == 1:
            tp += 1
        elif actual == 0 and predicted == 1:
            fp += 1
        elif actual == 0 and predicted == 0:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    fpr = fp / (fp + tn) if fp + tn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0

    return {
        "strategy": strategy,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_positive_rate": round(fpr, 4),
        "f1_score": round(f1, 4),
        "review_queue_size": tp + fp,
    }


def main():
    if not DB_PATH.is_file():
        raise FileNotFoundError(
            "Missing data/banking.db. Run: python -m src.pipeline"
        )

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT t.is_fraud, t.flagged, b.behavioral_flag
            FROM transactions t
            JOIN behavioral_signals b
              ON t.transaction_id = b.transaction_id
            ORDER BY t.transaction_id
        """).fetchall()

        total = conn.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

    if len(rows) != total:
        raise ValueError(
            "Missing behavioral signals. Run: python -m src.behavioral"
        )

    strategies = {
        "Risk Score >= 65": [(a, r) for a, r, b in rows],
        "Behavioral Only": [(a, b) for a, r, b in rows],
        "Combined OR": [(a, int(r or b)) for a, r, b in rows],
    }

    results = [
        calculate_metrics(records, name)
        for name, records in strategies.items()
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    for result in results:
        print(f"\n{result['strategy']}")
        print(f"  Precision: {result['precision']:.2%}")
        print(f"  Recall: {result['recall']:.2%}")
        print(f"  F1 Score: {result['f1_score']:.2%}")
        print(f"  False positives: {result['false_positives']}")
        print(f"  Investigation queue: {result['review_queue_size']}")

    print(f"\nSaved report: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
