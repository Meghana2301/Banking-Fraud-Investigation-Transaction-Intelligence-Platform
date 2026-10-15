import sqlite3
import tempfile
import unittest
from pathlib import Path
from src.pipeline import generate, load, report, risk_score


class PipelineTests(unittest.TestCase):
    def test_score_bounds(self):
        self.assertEqual(risk_score(2000, 'GB', 'online'), 95)
        self.assertEqual(risk_score(20, 'US', 'mobile'), 0)

    def test_end_to_end_and_idempotency(self):
        with tempfile.TemporaryDirectory() as folder:
            csv_path = Path(folder) / 'transactions.csv'
            db_path = Path(folder) / 'bank.db'
            generate(120, 7, csv_path)
            self.assertEqual(load(csv_path, db_path), 120)
            self.assertEqual(load(csv_path, db_path), 120)
            stats = report(db_path)
            self.assertEqual(stats['transactions'], 120)
            self.assertGreater(stats['total_amount'], 0)
            with sqlite3.connect(db_path) as conn:
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM transactions WHERE risk_score < 0 OR risk_score > 100').fetchone()[0], 0)

    def test_negative_amount_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'invalid.csv'
            path.write_text('transaction_id,customer_id,account_id,timestamp,amount,merchant_category,country,channel,is_fraud\n1,1,A00001,2026-01-01T00:00:00,-3,travel,US,online,0\n')
            with self.assertRaises(ValueError):
                load(path, Path(folder) / 'bank.db')


if __name__ == '__main__':
    unittest.main()
