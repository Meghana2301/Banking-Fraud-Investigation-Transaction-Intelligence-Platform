# Fraud-risk evaluation: beyond a basic fraud notebook

## Business question
How does a bank's investigation workload change when the fraud-risk threshold changes?

## Reproduce
```bash
python -m src.pipeline --rows 5000 --seed 42
python -m src.evaluation
python -m unittest discover -s tests -v
```

The evaluation calculates precision, recall, false-positive rate, and review queue size at several thresholds. It uses synthetic labels produced by the data generator, so these results **cannot** establish real-world fraud-detection performance.

## Assumptions and limitations
- Each transaction is independent in the initial simulator; it does not yet model longitudinal account behavior.
- The risk rules and labels share some generating factors, so evaluation is optimistically biased.
- There is no real investigation outcome, investigator capacity model, or verified monetary loss model yet.
- No sensitive personal data or employer data is used.

## Roadmap
1. Customer histories, merchant risk and burst detection with chronological validation.
2. Data contracts, late-arriving events, deduplication, and reconciliation.
3. Case-prioritization queues with review-capacity constraints and transparent cost assumptions.
4. dbt and Snowflake warehouse models; PySpark batch processing; Airflow orchestration.
5. Dashboard with case-level drilldown and threshold comparisons.

## Interview discussion
Explain the difference between a risk flag and confirmed fraud, the cost of false positives, why precision and recall trade off, and why synthetic evaluation is not production validation.
