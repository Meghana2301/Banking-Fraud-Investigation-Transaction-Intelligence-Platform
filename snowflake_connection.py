
import os
import snowflake.connector


def get_snowflake_connection():
    """Connect to Snowflake using a token from the environment."""

    token = os.environ.get("SNOWFLAKE_DBT_TOKEN")

    if not token:
        raise RuntimeError(
            "SNOWFLAKE_DBT_TOKEN is not configured."
        )

    connection = snowflake.connector.connect(
        account="DF75107.us-east-2.aws",
        user="BANKING_FRAUD_DBT_USER",
        authenticator="programmatic_access_token",
        token=token,
        warehouse="BANKING_FRAUD_WH",
        database="BANKING_FRAUD_DB",
        schema="MARTS",
        role="BANKING_FRAUD_DBT_ROLE",
        login_timeout=30,
    )

    return connection
