"""Quarantine invalid CSV rows; preserve valid records for controlled ingestion."""
import csv
import json
from datetime import datetime
from pathlib import Path
from src.quality import REQUIRED


def quarantine_csv(source, clean_path, rejects_path):
    source, clean_path, rejects_path = map(Path, (source, clean_path, rejects_path))
    if len({source.resolve(), clean_path.resolve(), rejects_path.resolve()}) != 3:
        raise ValueError("Input and output paths must be distinct")
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    rejects_path.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    accepted = rejected = 0
    with source.open(newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        if not set(REQUIRED).issubset(reader.fieldnames or []):
            raise ValueError("Input is missing required columns")
        with clean_path.open("w", newline="", encoding="utf-8") as good, rejects_path.open("w", encoding="utf-8") as bad:
            writer = csv.DictWriter(good, fieldnames=REQUIRED)
            writer.writeheader()
            for line, row in enumerate(reader, 2):
                reasons = []
                if any(row.get(k) is None or not str(row[k]).strip() for k in REQUIRED):
                    reasons.append("missing_value")
                else:
                    try:
                        if int(row["transaction_id"]) <= 0 or int(row["customer_id"]) <= 0:
                            raise ValueError()
                    except ValueError:
                        reasons.append("invalid_identifier")
                    try:
                        amount = float(row["amount"])
                        if not (0 <= amount < float("inf")):
                            raise ValueError()
                    except ValueError:
                        reasons.append("invalid_amount")
                    try:
                        datetime.fromisoformat(row["timestamp"])
                    except ValueError:
                        reasons.append("invalid_timestamp")
                    if row["is_fraud"] not in ("0", "1"):
                        reasons.append("invalid_label")
                    if row["transaction_id"] in seen:
                        reasons.append("duplicate_transaction_id")
                    else:
                        seen.add(row["transaction_id"])
                if reasons:
                    bad.write(json.dumps({"source_row": line, "reasons": reasons, "record": row}) + "\n")
                    rejected += 1
                else:
                    writer.writerow({k: row[k] for k in REQUIRED})
                    accepted += 1
    return {"accepted": accepted, "quarantined": rejected, "clean_csv": str(clean_path), "rejects_jsonl": str(rejects_path)}
