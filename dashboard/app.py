"""Interactive synthetic banking investigation dashboard.

Run:
  python -m src.pipeline --rows 5000 --seed 42
  python -m src.behavioral
  streamlit run dashboard/app.py
"""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB = Path(__file__).resolve().parents[1] / "data" / "banking.db"
st.set_page_config(page_title="Fraud Investigation | Banking Intelligence", layout="wide")
st.title("Banking Fraud Investigation & Transaction Intelligence")
st.caption("Portfolio demonstration using synthetic transactions. Flags and priorities are investigative aids, not confirmed fraud.")

if not DB.exists():
    st.warning("Database missing. Run: python -m src.pipeline --rows 5000 --seed 42")
    st.stop()


@st.cache_data(show_spinner=False)
def read_transactions(db_file, modified_time):
    with sqlite3.connect(db_file) as conn:
        has_signals = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='behavioral_signals'"
        ).fetchone()[0] > 0
        if has_signals:
            sql = """SELECT t.*, COALESCE(b.spending_spike,0) AS spending_spike,
                COALESCE(b.rapid_burst,0) AS rapid_burst,
                COALESCE(b.behavioral_flag,0) AS behavioral_flag,
                b.prior_median_amount
                FROM transactions t LEFT JOIN behavioral_signals b USING(transaction_id)"""
        else:
            sql = """SELECT t.*, 0 AS spending_spike, 0 AS rapid_burst,
                0 AS behavioral_flag, NULL AS prior_median_amount FROM transactions t"""
        return pd.read_sql_query(sql, conn), has_signals


df, has_signals = read_transactions(str(DB), DB.stat().st_mtime_ns)
if df.empty:
    st.info("No transactions are available yet.")
    st.stop()

df["date"] = pd.to_datetime(df["timestamp"]).dt.date
df["priority_score"] = (df["risk_score"] + 25 * df["spending_spike"] + 20 * df["rapid_burst"]).clip(upper=100)
df["review_candidate"] = ((df["risk_score"] >= 65) | (df["behavioral_flag"] == 1))
df["reason_codes"] = df.apply(
    lambda r: ", ".join(
        (["HEURISTIC_RISK"] if r["risk_score"] >= 65 else [])
        + (["SPENDING_SPIKE"] if r["spending_spike"] else [])
        + (["RAPID_BURST"] if r["rapid_burst"] else [])
    ), axis=1
)

if not has_signals:
    st.warning("Behavioral signals are not yet generated. Run: python -m src.behavioral")

st.sidebar.header("Investigation filters")
countries = st.sidebar.multiselect("Country", sorted(df["country"].unique()), default=sorted(df["country"].unique()))
channels = st.sidebar.multiselect("Channel", sorted(df["channel"].unique()), default=sorted(df["channel"].unique()))
min_risk = st.sidebar.slider("Minimum heuristic risk score", 0, 100, 0, 5)
capacity = st.sidebar.slider("Investigator review capacity", 1, 200, 25)
filtered = df[df["country"].isin(countries) & df["channel"].isin(channels) & (df["risk_score"] >= min_risk)].copy()

overview, investigations, behavior, quality = st.tabs(
    ["Overview", "Investigation queue", "Behavior analytics", "Data quality"]
)

with overview:
    a, b, c, d = st.columns(4)
    a.metric("Transactions", f"{len(filtered):,}")
    b.metric("Transaction value", f"${filtered['amount'].sum():,.2f}")
    c.metric("Review candidates", f"{int(filtered['review_candidate'].sum()):,}")
    d.metric("Candidate rate", f"{filtered['review_candidate'].mean():.1%}" if len(filtered) else "N/A")
    st.subheader("Daily transaction value")
    st.line_chart(filtered.groupby("date")["amount"].sum())
    st.subheader("Transaction value by merchant category")
    st.bar_chart(filtered.groupby("merchant_category")["amount"].sum())
    st.subheader("Heuristic risk distribution")
    st.bar_chart(filtered["risk_score"].value_counts().sort_index())

with investigations:
    st.subheader("Explainable investigation queue")
    st.caption("Priority = heuristic risk + 25 for spending spike + 20 for rapid burst (capped at 100). This is not a fraud probability.")
    candidates = filtered[filtered["review_candidate"]].sort_values(
        ["priority_score", "amount", "transaction_id"], ascending=[False, False, True]
    )
    selected = candidates.head(capacity)
    a, b, c = st.columns(3)
    a.metric("Eligible cases", f"{len(candidates):,}")
    b.metric("Selected for review", f"{len(selected):,}")
    c.metric("Deferred cases", f"{max(0, len(candidates) - len(selected)):,}")
    columns = ["transaction_id", "customer_id", "timestamp", "amount",
               "priority_score", "risk_score", "reason_codes", "country", "channel"]
    st.dataframe(selected[columns], use_container_width=True, hide_index=True)
    st.download_button("Download selected cases (CSV)", selected[columns].to_csv(index=False),
                       file_name="investigation_queue.csv", mime="text/csv", disabled=selected.empty)

with behavior:
    st.subheader("Historical behavioral signals")
    a, b, c = st.columns(3)
    a.metric("Spending spikes", f"{int(filtered['spending_spike'].sum()):,}")
    b.metric("Rapid bursts", f"{int(filtered['rapid_burst'].sum()):,}")
    c.metric("Behaviorally flagged", f"{int(filtered['behavioral_flag'].sum()):,}")
    st.caption("Signals use prior customer history in event-time order. Sparse history can limit spike detection.")
    behavioral = filtered[filtered["behavioral_flag"] == 1].sort_values(
        ["timestamp", "transaction_id"], ascending=[False, False]
    )
    st.dataframe(behavioral[["transaction_id", "customer_id", "timestamp", "amount",
                            "prior_median_amount", "spending_spike", "rapid_burst"]],
                 use_container_width=True, hide_index=True)

with quality:
    st.subheader("Database integrity and reconciliation")
    st.caption("This tab checks the loaded SQLite data. It does not inspect the separate quarantine JSONL file.")
    with sqlite3.connect(DB) as conn:
        stored_count, flagged, unflagged, negative = conn.execute(
            """SELECT COUNT(*), COALESCE(SUM(flagged),0),
            COALESCE(SUM(1-flagged),0),
            COALESCE(SUM(CASE WHEN amount < 0 THEN 1 ELSE 0 END),0)
            FROM transactions"""
        ).fetchone()
        duplicate_ids = conn.execute(
            "SELECT COUNT(*) FROM (SELECT transaction_id FROM transactions GROUP BY transaction_id HAVING COUNT(*) > 1)"
        ).fetchone()[0]
        signal_count = conn.execute("SELECT COUNT(*) FROM behavioral_signals").fetchone()[0] if has_signals else 0
    checks = pd.DataFrame([
        {"check": "Flag reconciliation", "status": "PASS" if stored_count == flagged + unflagged else "FAIL",
         "details": f"{stored_count} = {flagged} + {unflagged}"},
        {"check": "Duplicate transaction IDs", "status": "PASS" if duplicate_ids == 0 else "FAIL",
         "details": f"{duplicate_ids} duplicates"},
        {"check": "Nonnegative amounts", "status": "PASS" if negative == 0 else "FAIL",
         "details": f"{negative} invalid amounts"},
        {"check": "Behavioral signal coverage", "status": "PASS" if signal_count == stored_count else "NOT READY",
         "details": f"{signal_count}/{stored_count} rows"},
    ])
    st.dataframe(checks, use_container_width=True, hide_index=True)
    st.info("For source-file quality auditing, run python -m src.quality. Rejected records are stored separately by src.quarantine.")
