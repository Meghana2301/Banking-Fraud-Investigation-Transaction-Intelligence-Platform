"""End-to-end CI smoke checks for the banking analytics project.

Runs after synthetic data generation. Executes each reporting SQL statement,
checks reconciliation, evaluates risk metrics and imports the dashboard module.
"""
import importlib.util
import sqlite3
from pathlib import Path

from src.evaluation import evaluate
from src.pipeline import ROOT

DB = ROOT / "data" / "banking.db"
SQL = ROOT / "sql" / "analytics.sql"
DASHBOARD = ROOT / "dashboard" / "app.py"


def main():
    assert DB.is_file(), "Generate the synthetic database before smoke checks"
    with sqlite3.connect(DB) as conn:
        total = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        assert total == 5000, f"Expected 5000 synthetic transactions, found {total}"
        statements = [part.strip() for part in SQL.read_text(encoding="utf-8").split(";") if part.strip()]
        assert len(statements) >= 4, "Expected all four analytical SQL queries"
        for index, statement in enumerate(statements, 1):
            rows = conn.execute(statement).fetchall()
            assert rows, f"SQL query {index} returned no rows"
            print(f"SQL query {index}: OK ({len(rows)} rows)")
        count, flagged, unflagged = conn.execute(
            "SELECT COUNT(*), SUM(flagged), SUM(1-flagged) FROM transactions"
        ).fetchone()
        assert count == flagged + unflagged, "Flag reconciliation failed"
    evaluation = evaluate(DB)
    assert len(evaluation) == 4
    assert all(result["review_queue_size"] <= total for result in evaluation)
    assert DASHBOARD.is_file()
    # Import the dashboard with Streamlit's bare-mode runtime; it will execute
    # top-level UI code and database queries, but no browser is launched.
    spec = importlib.util.spec_from_file_location("banking_dashboard_smoke", DASHBOARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("Dashboard import and top-level execution: OK")
    print("End-to-end smoke checks passed")


if __name__ == "__main__":
    main()
