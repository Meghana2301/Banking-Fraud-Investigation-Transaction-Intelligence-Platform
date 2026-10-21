
import pandas as pd
import streamlit as st
import altair as alt

from snowflake_connection import get_snowflake_connection
import os
from pathlib import Path

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Banking Fraud | Risk Intelligence",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. PROFESSIONAL DARK THEME
# ============================================================

st.markdown("""
<style>
    .stApp {
        background-color: #0B1220;
        color: #F1F5F9;
    }

    .block-container {
        max-width: 1550px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #F1F5F9 !important;
        letter-spacing: -0.5px;
    }

    [data-testid="stSidebar"] {
        background-color: #101C2E;
        border-right: 1px solid #263850;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #182941, #111D30);
        border: 1px solid #2B405A;
        border-radius: 16px;
        padding: 20px;
    }

    [data-testid="stMetricLabel"] {
        color: #AFC2D8;
    }

    [data-testid="stMetricValue"] {
        color: #5EEAD4;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #2B405A;
        border-radius: 12px;
    }

    .eyebrow {
        color: #5EEAD4;
        font-size: 0.78rem;
        letter-spacing: 2px;
        font-weight: 700;
    }

    .subtitle {
        color: #AFC2D8;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    .section-heading {
        color: #F1F5F9;
        font-size: 1.3rem;
        font-weight: 700;
        margin-top: 0.7rem;
        margin-bottom: 0.8rem;
    }

    .info-panel {
        background: #14243A;
        border: 1px solid #2B405A;
        border-radius: 14px;
        padding: 20px;
        color: #D7E5F4;
    }

    hr {
        border-color: #2B405A;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. CHART COLORS
# ============================================================

TEAL = "#5EEAD4"
RED = "#FB7185"
AMBER = "#FBBF24"
BLUE = "#60A5FA"

PRIORITY_ORDER = [
    "P1 - URGENT",
    "P2 - HIGH",
    "P3 - REVIEW",
]

PRIORITY_COLORS = [RED, AMBER, TEAL]

RISK_ORDER = [
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
]

RISK_COLORS = [RED, AMBER, BLUE, TEAL]


# ============================================================
# PUBLIC DEMO DATA ACCESS
# ============================================================

@st.cache_data(show_spinner=False)
def load_demo_data():
    data_dir = Path(__file__).resolve().parent / "demo_data"

    daily = pd.read_csv(
        data_dir / "daily_transaction_intelligence.csv"
    )

    customers = pd.read_csv(
        data_dir / "customer_risk_summary.csv"
    )

    investigations = pd.read_csv(
        data_dir / "fraud_investigation_queue.csv"
    )

    return daily, customers, investigations

# ============================================================
# 4. SNOWFLAKE DATA ACCESS
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def run_query(query):
    """Execute a Snowflake SELECT query."""

    conn = get_snowflake_connection()

    try:
        cursor = conn.cursor()

        try:
            cursor.execute(query)

            rows = cursor.fetchall()

            columns = [
                col[0] for col in cursor.description
            ]

            return pd.DataFrame(
                rows,
                columns=columns,
            )

        finally:
            cursor.close()

    finally:
        conn.close()


@st.cache_data(ttl=300, show_spinner=False)
def load_dashboard_data():

    daily = run_query("""
        SELECT
            TRANSACTION_DATE,
            TOTAL_TRANSACTIONS,
            ACTIVE_CUSTOMERS,
            TOTAL_TRANSACTION_AMOUNT,
            FLAGGED_TRANSACTIONS,
            LABELED_FRAUD_TRANSACTIONS,
            FLAGGED_RATE_PCT,
            AVG_RISK_SCORE
        FROM BANKING_FRAUD_DB.MARTS.MART_DAILY_TRANSACTION_INTELLIGENCE
        ORDER BY TRANSACTION_DATE
    """)

    customers = run_query("""
        SELECT
            CUSTOMER_ID,
            TOTAL_TRANSACTIONS,
            TOTAL_TRANSACTION_AMOUNT,
            FLAGGED_TRANSACTIONS,
            LABELED_FRAUD_TRANSACTIONS,
            MAX_RISK_SCORE,
            CUSTOMER_RISK_LEVEL
        FROM BANKING_FRAUD_DB.MARTS.MART_CUSTOMER_RISK_SUMMARY
    """)

    investigations = run_query("""
        SELECT
            TRANSACTION_ID,
            CUSTOMER_ID,
            ACCOUNT_ID,
            TRANSACTION_TIMESTAMP,
            AMOUNT,
            MERCHANT_CATEGORY,
            COUNTRY,
            CHANNEL,
            RISK_SCORE,
            RISK_LEVEL,
            CUSTOMER_RISK_LEVEL,
            INVESTIGATION_PRIORITY
        FROM BANKING_FRAUD_DB.MARTS.MART_FRAUD_INVESTIGATION_QUEUE
    """)

    return daily, customers, investigations


# ============================================================
# 5. HEADER
# ============================================================

st.markdown(
    '<div class="eyebrow">RISK INTELLIGENCE / COMMAND CENTER</div>',
    unsafe_allow_html=True,
)

st.title("🏦 Banking Fraud Investigation")

st.markdown(
    '<div class="subtitle">'
    'Transaction Intelligence | Fraud Risk Monitoring | '
    'Investigation Command Center'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# 6. LOAD SNOWFLAKE DATA
# ============================================================

try:
    if DEMO_MODE:
        with st.spinner("Loading synthetic demo data..."):
            daily_df, customers_df, queue_df = load_demo_data()
    else:
        with st.spinner("Loading intelligence from Snowflake..."):
            daily_df, customers_df, queue_df = load_dashboard_data()

except Exception:
    st.error(
        "Unable to load dashboard data. "
        "Check your data source configuration."
    )
    st.stop()


if daily_df.empty:
    st.warning("No transaction data was found.")
    st.stop()


# ============================================================
# 7. DATA PREPARATION
# ============================================================

daily_df["TRANSACTION_DATE"] = pd.to_datetime(
    daily_df["TRANSACTION_DATE"]
)

queue_df["TRANSACTION_TIMESTAMP"] = pd.to_datetime(
    queue_df["TRANSACTION_TIMESTAMP"]
)

queue_df["TRANSACTION_DATE"] = (
    queue_df["TRANSACTION_TIMESTAMP"].dt.date
)

numeric_daily = [
    "TOTAL_TRANSACTIONS",
    "TOTAL_TRANSACTION_AMOUNT",
    "FLAGGED_TRANSACTIONS",
    "LABELED_FRAUD_TRANSACTIONS",
]

for column in numeric_daily:
    daily_df[column] = pd.to_numeric(
        daily_df[column],
        errors="coerce",
    ).fillna(0)

for column in ["AMOUNT", "RISK_SCORE"]:
    queue_df[column] = pd.to_numeric(
        queue_df[column],
        errors="coerce",
    )

customers_df["MAX_RISK_SCORE"] = pd.to_numeric(
    customers_df["MAX_RISK_SCORE"],
    errors="coerce",
)

min_date = daily_df["TRANSACTION_DATE"].min().date()
max_date = daily_df["TRANSACTION_DATE"].max().date()


# ============================================================
# 8. SIDEBAR FILTERS
# ============================================================

with st.sidebar:

    st.title("🛡️ Risk Control")
    st.caption("Fraud Intelligence Filters")

    st.divider()

    selected_dates = st.date_input(
        "Transaction Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    selected_priorities = st.multiselect(
        "Investigation Priority",
        options=PRIORITY_ORDER,
        default=PRIORITY_ORDER,
    )

    countries = sorted(
        queue_df["COUNTRY"].dropna().unique().tolist()
    )

    selected_countries = st.multiselect(
        "Transaction Country",
        options=countries,
        default=countries,
    )

    min_risk = st.slider(
        "Minimum Risk Score",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
    )

    selected_risk_levels = st.multiselect(
        "Customer Risk Level",
        options=RISK_ORDER,
        default=RISK_ORDER,
    )

    search_customer = st.text_input(
        "Search Customer ID",
        placeholder="Enter customer ID",
    )

    st.divider()

    if st.button(
        "🔄 Refresh Demo Data" if DEMO_MODE else "🔄 Refresh Snowflake Data",
        use_container_width=True,
    ):
        st.cache_data.clear()
        st.rerun()

    st.caption(
    (
        "Source: Synthetic CSV Snapshot (Snowflake/dbt Output)"
        if DEMO_MODE
        else "Source: Snowflake | Transformation: dbt"
    )
    + " | Application: Streamlit"
)


# ============================================================
# 9. APPLY FILTERS
# ============================================================

# Handle partially selected date ranges safely.
if len(selected_dates) == 2:
    start_date, end_date = selected_dates
elif len(selected_dates) == 1:
    start_date = selected_dates[0]
    end_date = selected_dates[0]
else:
    start_date, end_date = min_date, max_date


# Filter daily transaction data.
filtered_daily = daily_df[
    daily_df["TRANSACTION_DATE"].dt.date.between(
        start_date,
        end_date,
    )
].copy()


# Filter investigation cases.
filtered_queue = queue_df[
    queue_df["TRANSACTION_DATE"].between(
        start_date,
        end_date,
    )
].copy()

filtered_queue = filtered_queue[
    filtered_queue["INVESTIGATION_PRIORITY"].isin(
        selected_priorities
    )
]

filtered_queue = filtered_queue[
    filtered_queue["COUNTRY"].isin(
        selected_countries
    )
]

filtered_queue = filtered_queue[
    filtered_queue["RISK_SCORE"] >= min_risk
]

filtered_queue = filtered_queue[
    filtered_queue["CUSTOMER_RISK_LEVEL"].isin(
        selected_risk_levels
    )
]


# Filter customer risk data.
filtered_customers = customers_df[
    customers_df["CUSTOMER_RISK_LEVEL"].isin(
        selected_risk_levels
    )
].copy()


# Customer search applies to both datasets.
if search_customer.strip():

    customer_search = search_customer.strip()

    filtered_queue = filtered_queue[
        filtered_queue["CUSTOMER_ID"]
        .astype(str)
        .str.contains(
            customer_search,
            case=False,
            regex=False,
        )
    ]

    filtered_customers = filtered_customers[
        filtered_customers["CUSTOMER_ID"]
        .astype(str)
        .str.contains(
            customer_search,
            case=False,
            regex=False,
        )
    ]


# ============================================================
# 10. FRAUD MONITORING KPIs
# ============================================================

st.markdown(
    '<div class="section-heading">Fraud Monitoring Overview</div>',
    unsafe_allow_html=True,
)

total_transactions = int(
    filtered_daily["TOTAL_TRANSACTIONS"].sum()
)

flagged_transactions = int(
    filtered_daily["FLAGGED_TRANSACTIONS"].sum()
)

labeled_fraud = int(
    filtered_daily["LABELED_FRAUD_TRANSACTIONS"].sum()
)

total_customers = len(filtered_customers)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Transactions",
    f"{total_transactions:,}",
)

col2.metric(
    "Flagged for Review",
    f"{flagged_transactions:,}",
)

col3.metric(
    "Labeled Fraud",
    f"{labeled_fraud:,}",
)

col4.metric(
    "Matching Customers", 
    f"{total_customers:,}",
)

st.caption(
    "Transaction KPIs use the selected date range. "
    "Customer count uses customer risk and search filters. "
    "Investigation filters apply to flagged cases only."
)

st.divider()


# ============================================================
# 11. INVESTIGATION PRIORITY
# ============================================================

st.markdown(
    '<div class="section-heading">🚨 Investigation Priority</div>',
    unsafe_allow_html=True,
)

priority_counts = (
    filtered_queue["INVESTIGATION_PRIORITY"]
    .value_counts()
    .reindex(PRIORITY_ORDER, fill_value=0)
)

visible_priorities = [
    priority
    for priority in PRIORITY_ORDER
    if priority in selected_priorities
]

priority_df = pd.DataFrame({
    "Priority": visible_priorities,
    "Cases": [
        int(priority_counts[priority])
        for priority in visible_priorities
    ],
})

priority_left, priority_right = st.columns([1.5, 1])

with priority_left:

    if priority_df.empty:
        st.info("Select a priority to display the chart.")

    else:
        chart = (
            alt.Chart(priority_df)
            .mark_bar(
                cornerRadiusEnd=8,
                size=42,
            )
            .encode(
                x=alt.X(
                    "Priority:N",
                    sort=visible_priorities,
                    title=None,
                    axis=alt.Axis(labelAngle=0),
                ),
                y=alt.Y(
                    "Cases:Q",
                    title="Investigation Cases",
                ),
                color=alt.Color(
                    "Priority:N",
                    scale=alt.Scale(
                        domain=PRIORITY_ORDER,
                        range=PRIORITY_COLORS,
                    ),
                    legend=None,
                ),
                tooltip=[
                    "Priority:N",
                    "Cases:Q",
                ],
            )
            .properties(height=290)
        )

        st.altair_chart(
            chart,
            use_container_width=True,
        )

with priority_right:

    for priority, label, emoji in [
        ("P1 - URGENT", "P1 — Urgent", "🔴"),
        ("P2 - HIGH", "P2 — High", "🟠"),
        ("P3 - REVIEW", "P3 — Review", "🟢"),
    ]:

        if priority in selected_priorities:
            st.metric(
                f"{emoji} {label}",
                f"{int(priority_counts[priority]):,}",
            )

st.caption(
    f"Showing {len(filtered_queue):,} investigation cases "
    "matching the selected filters."
)

st.divider()


# ============================================================
# 12. DAILY TRANSACTION INTELLIGENCE
# ============================================================

st.markdown(
    '<div class="section-heading">📈 Daily Transaction Intelligence</div>',
    unsafe_allow_html=True,
)

trend_left, trend_right = st.columns([1.5, 1])

if filtered_daily.empty:
    st.info("No transaction data for the selected dates.")

else:

    with trend_left:

        st.markdown("**Transaction Volume Over Time**")

        volume_chart = (
            alt.Chart(filtered_daily)
            .mark_area(
                line={"color": TEAL},
                color=TEAL,
                opacity=0.22,
            )
            .encode(
                x=alt.X(
                    "TRANSACTION_DATE:T",
                    title="Transaction Date",
                ),
                y=alt.Y(
                    "TOTAL_TRANSACTIONS:Q",
                    title="Transactions",
                ),
                tooltip=[
                    "TRANSACTION_DATE:T",
                    "TOTAL_TRANSACTIONS:Q",
                ],
            )
            .properties(height=310)
        )

        st.altair_chart(
            volume_chart,
            use_container_width=True,
        )

    with trend_right:

        st.markdown("**Flagged Transactions Over Time**")

        flagged_chart = (
            alt.Chart(filtered_daily)
            .mark_bar(
                color=RED,
                cornerRadiusEnd=3,
            )
            .encode(
                x=alt.X(
                    "TRANSACTION_DATE:T",
                    title="Transaction Date",
                ),
                y=alt.Y(
                    "FLAGGED_TRANSACTIONS:Q",
                    title="Flagged Transactions",
                ),
                tooltip=[
                    "TRANSACTION_DATE:T",
                    "FLAGGED_TRANSACTIONS:Q",
                ],
            )
            .properties(height=310)
        )

        st.altair_chart(
            flagged_chart,
            use_container_width=True,
        )

st.caption(
    "Daily charts show all transactions within the "
    "selected date range, not only flagged cases."
)

st.divider()


# ============================================================
# 13. CUSTOMER RISK INTELLIGENCE
# ============================================================

st.markdown(
    '<div class="section-heading">👥 Customer Risk Intelligence</div>',
    unsafe_allow_html=True,
)

risk_counts = (
    filtered_customers["CUSTOMER_RISK_LEVEL"]
    .value_counts()
    .reindex(RISK_ORDER, fill_value=0)
)

visible_risks = [
    risk
    for risk in RISK_ORDER
    if risk in selected_risk_levels
]

risk_df = pd.DataFrame({
    "Risk Level": visible_risks,
    "Customers": [
        int(risk_counts[risk])
        for risk in visible_risks
    ],
})

risk_left, risk_right = st.columns([1, 1])

with risk_left:

    if risk_df.empty or risk_df["Customers"].sum() == 0:
        st.info("No customers match the selected filters.")

    else:
        risk_chart = (
            alt.Chart(risk_df)
            .mark_arc(innerRadius=65)
            .encode(
                theta=alt.Theta("Customers:Q"),
                color=alt.Color(
                    "Risk Level:N",
                    scale=alt.Scale(
                        domain=RISK_ORDER,
                        range=RISK_COLORS,
                    ),
                    legend=alt.Legend(
                        title="Customer Risk",
                    ),
                ),
                tooltip=[
                    "Risk Level:N",
                    "Customers:Q",
                ],
            )
            .properties(height=310)
        )

        st.altair_chart(
            risk_chart,
            use_container_width=True,
        )

with risk_right:

    st.markdown("**Customer Risk Summary**")

    st.dataframe(
        risk_df,
        hide_index=True,
        use_container_width=True,
    )

    st.metric(
        "Matching Customers",
        f"{len(filtered_customers):,}",
    )

st.caption(
    "Customer risk levels come from the dbt customer mart "
    "and summarize the full customer history. "
    "Date, country, and priority filters do not recalculate "
    "historical customer risk."
)

st.divider()


# ============================================================
# 14. FRAUD INVESTIGATION QUEUE
# ============================================================

st.markdown(
    '<div class="section-heading">🔎 Fraud Investigation Queue</div>',
    unsafe_allow_html=True,
)

st.caption(
    "Filter cases by date, priority, country, minimum risk "
    "score, customer risk level, and customer ID."
)

queue_col1, queue_col2, queue_col3 = st.columns(3)

queue_col1.metric(
    "Filtered Cases",
    f"{len(filtered_queue):,}",
)

queue_col2.metric(
    "Average Risk Score",
    (
        f"{filtered_queue['RISK_SCORE'].mean():.1f}"
        if not filtered_queue.empty
        else "N/A"
    ),
)

queue_col3.metric(
    "Total Flagged Amount",
    f"${filtered_queue['AMOUNT'].sum():,.2f}",
)

display_columns = [
    "TRANSACTION_ID",
    "CUSTOMER_ID",
    "TRANSACTION_TIMESTAMP",
    "AMOUNT",
    "COUNTRY",
    "CHANNEL",
    "RISK_SCORE",
    "RISK_LEVEL",
    "CUSTOMER_RISK_LEVEL",
    "INVESTIGATION_PRIORITY",
]


display_queue = (
    filtered_queue[display_columns]
    .sort_values(
        by=["RISK_SCORE", "TRANSACTION_TIMESTAMP"],
        ascending=[False, False],
    )
    .copy()
)

# Make column headings easier to understand.
display_queue = display_queue.rename(
    columns={
        "TRANSACTION_ID": "Transaction ID",
        "CUSTOMER_ID": "Customer ID",
        "TRANSACTION_TIMESTAMP": "Transaction Time",
        "AMOUNT": "Amount",
        "COUNTRY": "Country",
        "CHANNEL": "Channel",
        "RISK_SCORE": "Risk Score",
        "RISK_LEVEL": "Risk Level",
        "CUSTOMER_RISK_LEVEL": "Customer Risk",
        "INVESTIGATION_PRIORITY": "Priority",
    }
)

st.dataframe(
    display_queue,
    use_container_width=True,
    hide_index=True,
    height=420,
    column_config={
        "Transaction ID": st.column_config.NumberColumn(
            "Transaction ID",
            width="medium",
            format="%d",
        ),
        "Customer ID": st.column_config.NumberColumn(
            "Customer ID",
            width="medium",
            format="%d",
        ),
        "Transaction Time": st.column_config.DatetimeColumn(
            "Transaction Time",
            width="medium",
            format="YYYY-MM-DD HH:mm",
        ),
        "Amount": st.column_config.NumberColumn(
            "Amount",
            width="medium",
            format="$%.2f",
        ),
        "Country": st.column_config.TextColumn(
            "Country",
            width="small",
        ),
        "Channel": st.column_config.TextColumn(
            "Channel",
            width="medium",
        ),
        "Risk Score": st.column_config.NumberColumn(
            "Risk Score",
            width="small",
            format="%.0f",
        ),
        "Risk Level": st.column_config.TextColumn(
            "Risk Level",
            width="medium",
        ),
        "Customer Risk": st.column_config.TextColumn(
            "Customer Risk",
            width="medium",
        ),
        "Priority": st.column_config.TextColumn(
            "Priority",
            width="medium",
        ),
    },
)

st.download_button(
    label="⬇️ Download Filtered Investigation Cases",
    data=display_queue.to_csv(index=False),
    file_name="fraud_investigation_queue.csv",
    mime="text/csv",
)

st.divider()



# ============================================================
# 15. FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        background-color: #14243A;
        border: 1px solid #2B405A;
        border-radius: 14px;
        padding: 24px;
    ">
        <h3 style="margin-top: 0; color: #F1F5F9;">
            Banking Fraud Investigation & Transaction Intelligence Platform
        </h3>
        <p style="color: #AFC2D8;">
            <strong>Architecture:</strong>
            Python → Snowflake RAW → dbt STAGING →
            dbt MARTS → Streamlit
        </p>
        <p style="color: #AFC2D8; margin-bottom: 0;">
            Portfolio demonstration using synthetic banking data.
            Risk flags are analytical review signals,
            not confirmed fraud determinations.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
