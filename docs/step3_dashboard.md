# Step 3 — Interactive investigation dashboard

## Start the application

```bash
pip install -r requirements.txt
python -m src.pipeline --rows 5000 --seed 42
python -m src.behavioral
streamlit run dashboard/app.py
```

Open the local Streamlit URL printed in the terminal (usually http://localhost:8501).

## Sections
1. **Overview** — transactions, total amount, review candidates, candidate rate, daily value, category breakdown and risk distribution.
2. **Investigation queue** — configurable review capacity, priority scores, explainable reason codes and downloadable case list.
3. **Behavior analytics** — spending spikes, rapid bursts, and transaction-level historical baselines.
4. **Data quality** — SQLite reconciliation, duplicate ID checks, nonnegative amounts and feature coverage.

Country, channel, and minimum heuristic risk filters affect the overview and investigation analytics. The data-quality checks intentionally cover the full loaded database.

## Interpreting the results
- Review candidates are selected when heuristic risk is at least 65 or a behavioral signal is present.
- Priority score is heuristic risk plus 25 for a spending spike and 20 for a rapid burst, capped at 100.
- Priority is an operational ranking, not a calibrated fraud probability.
- Quarantine is a separate ingestion utility; this dashboard does not display the rejection log.
- All data is synthetic and fraud labels are simulator-generated.

## Validation
The GitHub workflow imports and executes the dashboard module without a browser after generating the database and behavioral signals. This is a smoke test, not a visual or browser-level test. For the full experience, launch Streamlit locally and interact with the filters, tabs, and CSV download.
