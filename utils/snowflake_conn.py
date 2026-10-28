import os

import snowflake.connector
from dotenv import load_dotenv


load_dotenv()

def get_snowflake_connection():

    print(f"os.get = {os.getenv('SNOWFLAKE_ACCOUNT')}\n{os.getenv('SNOWFLAKE_PAT')}\n{os.getenv('SNOWFLAKE_USER')}")
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),

        password=os.getenv("SNOWFLAKE_PAT"),

        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        role=os.getenv("SNOWFLAKE_ROLE"),
    )

    return conn

def fetch_remote_data(query):
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query)

        rows = cursor.fetchall()

        columns = [
            column[0]
            for column in cursor.description
        ]

        return pl.DataFrame(
            rows,
            schema=columns,
            orient="row",
        )

    finally:
        cursor.close()
        conn.close()