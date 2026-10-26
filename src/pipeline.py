"""Reproducible synthetic banking analytics pipeline; no real customer data."""
import argparse
import csv
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import closing

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ['groceries', 'travel', 'fuel', 'electronics', 'restaurants', 'utilities']


def generate(n=5000, seed=42, output=None):
    random.seed(seed)
    output = Path(output or ROOT / 'data' / 'transactions.csv')
    output.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 1, 1)
    with output.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'customer_id', 'account_id', 'timestamp', 'amount', 'merchant_category', 'country', 'channel', 'is_fraud'])
        for i in range(1, n + 1):
            customer = random.randint(1, 600)
            amount = round(random.lognormvariate(3.8, 1.1), 2)
            unusual = random.random() < 0.035
            if unusual:
                amount = round(amount + random.uniform(800, 4500), 2)
            country = 'US' if random.random() < (0.55 if unusual else 0.96) else random.choice(['CA', 'GB', 'MX'])
            channel = random.choice(['card_present', 'online', 'mobile'])
            fraud = int(unusual and (country != 'US' or random.random() < 0.35))
            timestamp = start + timedelta(minutes=random.randint(0, 120 * 24 * 60))
            writer.writerow([i, customer, f'A{customer:05d}', timestamp.isoformat(timespec='seconds'), amount,
                             random.choice(CATEGORIES), country, channel, fraud])
    return output


def risk_score(amount, country, channel):
    """Transparent heuristic, not a production fraud decision model."""
    score = (50 if amount >= 1000 else 25 if amount >= 500 else 0)
    score += 30 if country != 'US' else 0
    score += 15 if channel == 'online' else 0
    return min(score, 100)


def load(csv_path=None, db_path=None):
    csv_path = Path(csv_path or ROOT / 'data' / 'transactions.csv')
    db_path = Path(db_path or ROOT / 'data' / 'banking.db')
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            conn.executescript("""CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL, account_id TEXT NOT NULL,
                timestamp TEXT NOT NULL, amount REAL NOT NULL CHECK(amount >= 0),
                merchant_category TEXT NOT NULL, country TEXT NOT NULL, channel TEXT NOT NULL,
                is_fraud INTEGER NOT NULL CHECK(is_fraud IN (0,1)), risk_score INTEGER NOT NULL,
                flagged INTEGER NOT NULL CHECK(flagged IN (0,1)));
                CREATE INDEX IF NOT EXISTS idx_txn_timestamp ON transactions(timestamp);
                CREATE INDEX IF NOT EXISTS idx_txn_customer ON transactions(customer_id);""")
            with csv_path.open(newline='', encoding='utf-8') as f:
                rows = []
                seen = set()
                for row in csv.DictReader(f):
                    tid = int(row['transaction_id'])
                    if tid in seen:
                        raise ValueError(f'duplicate transaction_id: {tid}')
                    seen.add(tid)
                    amount = float(row['amount'])
                    if amount < 0:
                        raise ValueError('negative transaction amount')
                    score = risk_score(amount, row['country'], row['channel'])
                    rows.append((tid, int(row['customer_id']), row['account_id'], row['timestamp'], amount,
                                 row['merchant_category'], row['country'], row['channel'], int(row['is_fraud']),
                                 score, int(score >= 65)))
            conn.executemany('INSERT OR REPLACE INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?)', rows)
            return len(rows)


def report(db_path=None):
    db_path = Path(db_path or ROOT / 'data' / 'banking.db')
    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            count, total, flagged, fraud = conn.execute("""SELECT COUNT(*), ROUND(SUM(amount),2),
                 SUM(flagged), SUM(is_fraud) FROM transactions""").fetchone()
            return {'transactions': count, 'total_amount': total, 'flagged': flagged, 'synthetic_fraud_labels': fraud}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rows', type=int, default=5000)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    if args.rows < 1:
        parser.error('--rows must be positive')
    path = generate(args.rows, args.seed)
    print(f'Generated {args.rows} synthetic transactions: {path}')
    print(f'Loaded {load(path)} transactions')
    print(report())


if __name__ == '__main__':
    main()
