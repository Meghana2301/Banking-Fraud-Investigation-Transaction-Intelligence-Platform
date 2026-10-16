import csv
import tempfile
import unittest
from pathlib import Path

from src.behavioral import score_behavior
from src.quality import audit_csv
from src.pipeline import generate


class BehavioralTests(unittest.TestCase):
    def test_spike_uses_prior_history_only(self):
        rows = [{"transaction_id": i, "customer_id": 1,
                 "timestamp": f"2026-01-01T{i:02d}:00:00", "amount": amount}
                for i, amount in enumerate([10, 12, 9, 11, 10, 500], 1)]
        result = score_behavior(list(reversed(rows)))
        self.assertEqual([r["spending_spike"] for r in result], [0, 0, 0, 0, 0, 1])
        self.assertEqual(result[-1]["prior_transaction_count"], 5)
        self.assertEqual(result[-1]["prior_median_amount"], 10)

    def test_burst_and_customer_isolation(self):
        rows = [
            {"transaction_id": 1, "customer_id": 1, "timestamp": "2026-01-01T10:00:00", "amount": 10},
            {"transaction_id": 2, "customer_id": 1, "timestamp": "2026-01-01T10:04:00", "amount": 10},
            {"transaction_id": 3, "customer_id": 2, "timestamp": "2026-01-01T10:05:00", "amount": 10},
            {"transaction_id": 4, "customer_id": 1, "timestamp": "2026-01-01T10:08:00", "amount": 10},
        ]
        results = {r["transaction_id"]: r for r in score_behavior(rows)}
        self.assertEqual(results[4]["rapid_burst"], 1)
        self.assertEqual(results[3]["rapid_burst"], 0)

    def test_quality_generated_csv(self):
        with tempfile.TemporaryDirectory() as folder:
            path = generate(30, 5, Path(folder) / "tx.csv")
            result = audit_csv(path)
            self.assertTrue(result["valid"], result["issues"])
            self.assertEqual(result["rows"], 30)

    def test_quality_duplicate_and_invalid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            with path.open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["transaction_id", "customer_id", "account_id", "timestamp", "amount",
                                 "merchant_category", "country", "channel", "is_fraud"])
                writer.writerow([1, 1, "A1", "2026-01-01T00:00:00", 10, "fuel", "US", "online", 0])
                writer.writerow([1, 1, "A1", "not-a-date", -1, "fuel", "US", "online", 0])
            issues = audit_csv(path)["issues"]
            reasons = {item["reason"] for item in issues}
            self.assertTrue({"duplicate_transaction_id", "invalid_amount", "invalid_timestamp"} <= reasons)


if __name__ == "__main__":
    unittest.main()
