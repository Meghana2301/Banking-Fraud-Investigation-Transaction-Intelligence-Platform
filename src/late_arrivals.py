"""Recompute historical behavioral features after late transaction arrival.

Event-time recomputation is deterministic and includes previously loaded
transactions; it does not represent an online streaming watermark.
"""
import json
from pathlib import Path
from src.pipeline import load
from src.behavioral import analyze


def ingest_late(csv_path, db_path):
    db_path = Path(db_path)
    loaded = load(csv_path, db_path)
    result = analyze(db_path)
    return {"ingested": loaded, "recomputed": result["analyzed"], "behavioral_flags": result["behavioral_flags"]}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--db", default="data/banking.db")
    args = parser.parse_args()
    print(json.dumps(ingest_late(args.csv_path, args.db), indent=2))
