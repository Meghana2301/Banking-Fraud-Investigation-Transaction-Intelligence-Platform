"""Historical customer behavior signals, computed without future-data leakage.

Usage: python -m src.behavioral
Signals are investigation aids, not fraud determinations.
"""
import csv
import json
import sqlite3
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median

from src.pipeline import ROOT


def score_behavior(rows, min_history=5, burst_count=3, burst_minutes=10, spike_multiplier=4):
    """Return one feature record per transaction in event-time order.

    Input rows have transaction_id, customer_id, timestamp and amount.
    Only earlier transactions are used as a baseline. Identical timestamps
    are ordered by transaction_id for deterministic processing.
    """
    ordered = sorted(rows, key=lambda r: (r["timestamp"], int(r["transaction_id"])))
    history = defaultdict(list)
    windows = defaultdict(deque)
    results = []
    for row in ordered:
        customer = str(row["customer_id"])
        amount = float(row["amount"])
        when = datetime.fromisoformat(row["timestamp"])
        prior = history[customer]
        recent = windows[customer]
        cutoff = when - timedelta(minutes=burst_minutes)
        while recent and recent[0] < cutoff:
            recent.popleft()
        baseline = median(prior) if len(prior) >= min_history else None
        spike = baseline is not None and amount >= max(100.0, baseline * spike_multiplier)
        burst = len(recent) + 1 >= burst_count
        results.append({
            "transaction_id": int(row["transaction_id"]),
            "customer_id": customer,
            "prior_transaction_count": len(prior),
            "prior_median_amount": round(baseline, 2) if baseline is not None else None,
            "spending_spike": int(spike),
            "rapid_burst": int(burst),
            "behavioral_flag": int(spike or burst),
        })
        prior.append(amount)
        recent.append(when)
    return results


def analyze(db_path=None):
    db_path = Path(db_path or ROOT / "data" / "banking.db")
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(row) for row in conn.execute(
            "SELECT transaction_id, customer_id, timestamp, amount FROM transactions"
        )]
        signals = score_behavior(rows)
        conn.execute("""CREATE TABLE IF NOT EXISTS behavioral_signals (
            transaction_id INTEGER PRIMARY KEY,
            customer_id TEXT NOT NULL,
            prior_transaction_count INTEGER NOT NULL,
            prior_median_amount REAL,
            spending_spike INTEGER NOT NULL,
            rapid_burst INTEGER NOT NULL,
            behavioral_flag INTEGER NOT NULL,
            FOREIGN KEY(transaction_id) REFERENCES transactions(transaction_id)
        )""")
        conn.execute("DELETE FROM behavioral_signals")
        conn.executemany("""INSERT INTO behavioral_signals VALUES (
            :transaction_id, :customer_id, :prior_transaction_count,
            :prior_median_amount, :spending_spike, :rapid_burst, :behavioral_flag
        )""", signals)
    return {"analyzed": len(signals), "behavioral_flags": sum(x["behavioral_flag"] for x in signals),
            "spikes": sum(x["spending_spike"] for x in signals),
            "bursts": sum(x["rapid_burst"] for x in signals)}


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2))
