"""Run with: streamlit run dashboard/app.py"""
import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

DB = Path(__file__).resolve().parents[1] / 'data' / 'banking.db'
st.set_page_config(page_title='Banking Risk Analytics', layout='wide')
st.title('Banking Transaction & Fraud Risk Analytics')
st.caption('Demonstration only — fully synthetic data; risk flags are not fraud determinations.')
if not DB.exists():
    st.info('First run: python -m src.pipeline')
    st.stop()
with sqlite3.connect(DB) as conn:
    df = pd.read_sql_query('SELECT * FROM transactions', conn)
df['date'] = pd.to_datetime(df['timestamp']).dt.date
countries = st.multiselect('Countries', sorted(df.country.unique()), default=sorted(df.country.unique()))
df = df[df.country.isin(countries)]
a, b, c, d = st.columns(4)
a.metric('Transactions', f'{len(df):,}')
b.metric('Total value', f'${df.amount.sum():,.2f}')
c.metric('Flagged for review', f'{df.flagged.sum():,}')
d.metric('Flag rate', f'{df.flagged.mean():.1%}' if len(df) else 'N/A')
st.subheader('Daily transaction value')
st.line_chart(df.groupby('date').amount.sum())
st.subheader('Transaction value by merchant category')
st.bar_chart(df.groupby('merchant_category').amount.sum())
st.subheader('Flagged transactions (synthetic)')
st.dataframe(df[df.flagged == 1].sort_values('risk_score', ascending=False).head(100), use_container_width=True)
