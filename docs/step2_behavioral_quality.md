# Step 2 — Behavioral Fraud Signals and Data Quality

## Run locally
```bash
python -m unittest discover -s tests -v
python -m src.pipeline --rows 5000 --seed 42
python -m src.quality
python -m src.behavioral
```

## Behavioral signals
The analysis sorts all transactions by event timestamp and transaction ID. It evaluates each customer independently:

- **Spending spike:** At least five earlier transactions exist and the current amount is at least four times the customer's previous median, with a minimum of $100.
- **Rapid burst:** At least three transactions for the same customer occur within an inclusive ten-minute lookback window.
- **Behavioral flag:** Either signal is present.

The pipeline writes results to the SQLite table `behavioral_signals`. Re-running analysis replaces the feature table rows, rather than appending duplicates. The original `transactions` table is unchanged.

**Important limitation:** Equal timestamps are ordered by transaction ID. In a real event-streaming system, ingestion timestamps, late arrivals, and event corrections need additional treatment. The simulator does not deliberately create customer-specific burst scenarios; the rules are tested with crafted examples instead.

## Data-quality audit
`python -m src.quality` validates the synthetic CSV and reports:
- missing required columns and values
- duplicate transaction IDs
- invalid identifiers, negative or non-numeric amounts
- invalid ISO timestamps and labels other than 0/1

This is a **reporting audit**: it does not yet quarantine bad records or automatically block ingestion. The current loader has some independent validations. Consolidating the audit with ingestion rejection/quarantine is a subsequent enhancement.

## Why it matters in interviews
Historical baselines reduce dependence on a single fixed amount threshold. Tests demonstrate temporal ordering and customer isolation. Explain false positives, cold-start customers, and the need for verified fraud labels before any production use.

## Current status
GitHub Actions runs unit tests, the synthetic pipeline, the CSV quality audit, behavioral feature generation, SQL checks, and dashboard import checks. A passing workflow validates this integration; a browser-level dashboard test is still outstanding.
