# python/ingest_stock_prices.py (FIXED VERSION)

import yfinance as yf
import pandas as pd
from db_connection import get_connection
import time

TICKERS    = ['AAPL','MSFT','XOM','NEE','JPM','TSLA','JNJ','AMZN','CVX','UL']
START_DATE = "2021-01-01"
END_DATE   = "2023-12-31"

def load_to_sql():
    conn   = get_connection()
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM stock_prices")
    conn.commit()
    print("🗑️  Cleared existing stock_prices data\n")

    total_rows = 0

    for ticker in TICKERS:
        try:
            # ── Download one ticker at a time ──────────────────
            df = yf.download(
                ticker,
                start=START_DATE,
                end=END_DATE,
                auto_adjust=True,
                progress=False  # suppress progress bar per ticker
            )

            if df.empty:
                print(f"  ⚠️  {ticker}: No data returned — skipping")
                continue

            # ── Flatten columns if MultiIndex ──────────────────
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df[['Open','High','Low','Close','Volume']].dropna()
            rows_for_ticker = 0

            for date, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO stock_prices
                        (ticker, price_date, open_price, high_price,
                         low_price, close_price, volume, adj_close)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    ticker,
                    date.strftime('%Y-%m-%d'),
                    round(float(row['Open']),  4),
                    round(float(row['High']),  4),
                    round(float(row['Low']),   4),
                    round(float(row['Close']), 4),
                    int(row['Volume']),
                    round(float(row['Close']), 4)
                )
                rows_for_ticker += 1

            conn.commit()
            total_rows += rows_for_ticker
            print(f"  ✅ {ticker}: {rows_for_ticker} rows inserted")

            # Small delay to avoid yfinance rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ {ticker}: Failed — {e}")

    conn.close()
    print(f"\n🎉 Total rows inserted into stock_prices: {total_rows}")

if __name__ == "__main__":
    load_to_sql()