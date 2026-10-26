"""Explainable, capacity-limited investigation queue for synthetic transactions."""
import json
import sqlite3
from pathlib import Path
from src.pipeline import ROOT
from contextlib import closing


def prioritize(db_path=None, capacity=50):
    if capacity < 0:
        raise ValueError("capacity must not be negative")
    db_path = Path(db_path or ROOT / "data" / "banking.db")
    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            conn.row_factory = sqlite3.Row
            records = conn.execute("""SELECT t.transaction_id, t.customer_id, t.timestamp,
                t.amount, t.risk_score, t.flagged, t.country, t.channel,
                COALESCE(b.spending_spike, 0) AS spending_spike,
                COALESCE(b.rapid_burst, 0) AS rapid_burst
                FROM transactions t LEFT JOIN behavioral_signals b
                ON t.transaction_id = b.transaction_id""").fetchall()
    queue = []
    for row in records:
        reasons = []
        if row["risk_score"] >= 65:
            reasons.append("HEURISTIC_RISK")
        if row["spending_spike"]:
            reasons.append("SPENDING_SPIKE")
        if row["rapid_burst"]:
            reasons.append("RAPID_BURST")
        if not reasons:
            continue
        priority = min(100, row["risk_score"] + 25 * row["spending_spike"] + 20 * row["rapid_burst"])
        queue.append({"transaction_id": row["transaction_id"], "customer_id": row["customer_id"],
                      "timestamp": row["timestamp"], "amount": row["amount"],
                      "priority_score": priority, "reason_codes": reasons})
    queue.sort(key=lambda r: (-r["priority_score"], -r["amount"], r["transaction_id"]))
    return {"candidate_count": len(queue), "capacity": capacity, "selected_count": min(capacity, len(queue)),
            "deferred_count": max(0, len(queue) - capacity), "cases": queue[:capacity]}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--capacity", type=int, default=50)
    args = parser.parse_args()
    result = prioritize(capacity=args.capacity)
    print(json.dumps(result, indent=2))
