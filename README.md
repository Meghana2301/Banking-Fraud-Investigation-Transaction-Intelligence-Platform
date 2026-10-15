# Banking Fraud Investigation & Transaction Intelligence Platform

An independent, reproducible portfolio project built with **synthetic banking data only**.

## Architecture

Seeded synthetic transactions → Python validation and fraud-risk rules → SQLite analytics database → SQL reporting → Streamlit dashboard.

## Quick start

```bash
python -m src.pipeline --rows 5000 --seed 42
python -m unittest discover -s tests -v
python -m pip install -r requirements.txt
streamlit run dashboard/app.py
```

The pipeline generates 5,000 synthetic transactions by default. Risk flags mean *review needed*, not confirmed fraud.

## Current scope

- Synthetic transaction generation
- Rule-based risk scoring
- SQLite analytical warehouse and SQL reports
- Streamlit dashboard
- Automated unit tests and GitHub Actions

## Planned enhancements (not yet implemented)

Snowflake, dbt, Airflow, PySpark, Power BI, and machine-learning evaluation.

**Disclaimer:** This is an independent portfolio demonstration, not a real bank deployment. No real banking/customer data or proprietary employer code is used.
