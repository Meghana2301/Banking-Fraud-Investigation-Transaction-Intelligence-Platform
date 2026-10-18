# Step 4: Snowflake + dbt

Snowflake source: `BANKING_FRAUD_DB.RAW.TRANSACTIONS` (synthetic data only).

The dbt staging model reproduces the Python pipeline's transparent risk heuristic. `IS_FRAUD` is a synthetic label; `FLAGGED` is a review signal, not a fraud determination.

## Run locally

Install `dbt-snowflake`, configure a local `banking_fraud` profile in `~/.dbt/profiles.yml` using your own Snowflake connection and `BANKING_FRAUD_WH`, then run:

```bash
dbt debug
dbt run --select stg_transactions
dbt test --select stg_transactions source:raw
```

Keep `profiles.yml`, passwords, tokens, and private keys out of GitHub. For a least-privilege production setup, use a dedicated dbt role rather than `ACCOUNTADMIN`.

The model materializes as a view in the profile's target schema unless you configure a custom schema. Validate 5,000 records and 114 flagged rows against the manually created `BANKING_FRAUD_DB.STAGING.STG_TRANSACTIONS` view before replacing it.
