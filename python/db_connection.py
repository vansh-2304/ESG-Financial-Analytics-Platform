# python/db_connection.py
# Central database connection — imported by all other scripts

import pyodbc
import pandas as pd

def get_connection():
    """
    Returns a pyodbc connection to ESGFinancialPlatform.
    Uses Windows Authentication (no username/password needed).
    """
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=VANSH;"          # Your server name from SSMS
        "DATABASE=ESGFinancialPlatform;"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

def run_query(sql):
    """Run a SELECT query and return a pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql(sql, conn)
    conn.close()
    return df

def execute_statement(sql, params=None):
    """Run INSERT/UPDATE/DELETE statements."""
    conn = get_connection()
    cursor = conn.cursor()
    if params:
        cursor.executemany(sql, params)
    else:
        cursor.execute(sql)
    conn.commit()
    conn.close()

# Quick connection test
if __name__ == "__main__":
    try:
        conn = get_connection()
        print("✅ Connected to ESGFinancialPlatform successfully!")
        conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")