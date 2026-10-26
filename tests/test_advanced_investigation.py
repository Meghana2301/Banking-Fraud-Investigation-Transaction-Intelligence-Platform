from contextlib import closing
import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.behavioral import analyze
from src.investigation import prioritize
from src.late_arrivals import ingest_late
from src.pipeline import generate, load
from src.quarantine import quarantine_csv
from src.quality import REQUIRED


class AdvancedInvestigationTests(unittest.TestCase):
    def test_quarantine_preserves_valid_and_records_reasons(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, clean, rejects = (root / n for n in ("raw.csv", "clean.csv", "rejects.jsonl"))
            with raw.open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(REQUIRED)
                writer.writerow([1, 1, "A1", "2026-01-01T00:00:00", 10, "fuel", "US", "online", 0])
                writer.writerow([1, 1, "A1", "2026-01-01T00:01:00", 20, "fuel", "US", "online", 0])
                writer.writerow([3, 1, "A1", "bad-time", -10, "fuel", "US", "online", 0])
            result = quarantine_csv(raw, clean, rejects)
            self.assertEqual((result["accepted"], result["quarantined"]), (1, 2))
            reasons = [set(json.loads(line)["reasons"]) for line in rejects.read_text().splitlines()]
            self.assertIn("duplicate_transaction_id", reasons[0])
            self.assertTrue({"invalid_timestamp", "invalid_amount"} <= reasons[1])
            self.assertEqual(load(clean, root / "bank.db"), 1)

    def test_late_event_recomputes_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "bank.db"
            raw = generate(5, 11, root / "seed.csv")
            load(raw, db)
            analyze(db)
            with closing(sqlite3.connect(db)) as conn:
                first = conn.execute("SELECT MIN(timestamp) FROM transactions").fetchone()[0]
                customer = conn.execute("SELECT customer_id FROM transactions LIMIT 1").fetchone()[0]
            late = root / "late.csv"
            with late.open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(REQUIRED)
                writer.writerow([999, customer, f"A{customer:05d}", "2025-01-01T00:00:00",
                                 50, "fuel", "US", "online", 0])
            result = ingest_late(late, db)
            self.assertEqual(result["recomputed"], 6)
            with closing(sqlite3.connect(db)) as conn:
                self.assertEqual(conn.execute(
                    "SELECT prior_transaction_count FROM behavioral_signals WHERE transaction_id=999"
                ).fetchone()[0], 0)

    def test_investigation_capacity_and_reason_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = generate(100, 7, root / "seed.csv")
            db = root / "bank.db"
            load(csv_path, db)
            analyze(db)
            result = prioritize(db, capacity=3)
            self.assertLessEqual(result["selected_count"], 3)
            self.assertEqual(result["candidate_count"], result["selected_count"] + result["deferred_count"])
            self.assertTrue(all(case["reason_codes"] for case in result["cases"]))
            self.assertEqual(result["cases"], sorted(result["cases"],
                key=lambda case: (-case["priority_score"], -case["amount"], case["transaction_id"])))
            with self.assertRaises(ValueError):
                prioritize(db, capacity=-1)


if __name__ == "__main__":
    unittest.main()
