"""Validate incoming synthetic transaction CSV before loading it into the warehouse."""
import csv
import json
from datetime import datetime
from pathlib import Path
from src.pipeline import ROOT

REQUIRED = ("transaction_id", "customer_id", "account_id", "timestamp", "amount",
            "merchant_category", "country", "channel", "is_fraud")


def audit_csv(path):
    issues = []
    seen = set()
    count = 0
    with Path(path).open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing_columns = sorted(set(REQUIRED) - set(reader.fieldnames or []))
        if missing_columns:
            return {"rows": 0, "valid": False, "issues": [{"row": 1, "reason": "missing_columns", "detail": missing_columns}]}
        for line, row in enumerate(reader, 2):
            count += 1
            for field in REQUIRED:
                if row[field] is None or not row[field].strip():
                    issues.append({"row": line, "reason": "missing_value", "field": field})
            if any(row[field] is None or not row[field].strip() for field in REQUIRED):
                continue
            tid = row["transaction_id"]
            if tid in seen:
                issues.append({"row": line, "reason": "duplicate_transaction_id", "value": tid})
            seen.add(tid)
            try:
                if int(tid) <= 0 or int(row["customer_id"]) <= 0:
                    raise ValueError()
            except ValueError:
                issues.append({"row": line, "reason": "invalid_identifier"})
            try:
                if float(row["amount"]) < 0:
                    raise ValueError()
            except ValueError:
                issues.append({"row": line, "reason": "invalid_amount"})
            try:
                datetime.fromisoformat(row["timestamp"])
            except ValueError:
                issues.append({"row": line, "reason": "invalid_timestamp"})
            if row["is_fraud"] not in ("0", "1"):
                issues.append({"row": line, "reason": "invalid_label"})
    return {"rows": count, "valid": not issues, "issue_count": len(issues), "issues": issues}


if __name__ == "__main__":
    path = ROOT / "data" / "transactions.csv"
    print(json.dumps(audit_csv(path), indent=2))
