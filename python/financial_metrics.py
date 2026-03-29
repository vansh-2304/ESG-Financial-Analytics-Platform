# python/financial_metrics.py
# Computes key financial ratios and exports to CSV

import pandas as pd
import numpy as np
from db_connection import run_query

def compute_metrics():
    # Load financials + company info
    df = run_query("""
        SELECT
            c.ticker, c.company_name, c.sector, c.market_cap_bn,
            f.fiscal_year, f.revenue_mn, f.gross_profit_mn,
            f.ebitda_mn, f.net_income_mn, f.eps,
            f.total_assets_mn, f.total_debt_mn,
            f.free_cash_flow_mn, f.roe
        FROM financials f
        JOIN companies c ON f.ticker = c.ticker
        ORDER BY c.ticker, f.fiscal_year
    """)

    # ── Margin Metrics ──────────────────────────────────────────
    df['gross_margin_pct'] = (
        df['gross_profit_mn'] / df['revenue_mn'].replace(0, np.nan) * 100
    ).round(2)

    df['ebitda_margin_pct'] = (
        df['ebitda_mn'] / df['revenue_mn'].replace(0, np.nan) * 100
    ).round(2)

    df['net_margin_pct'] = (
        df['net_income_mn'] / df['revenue_mn'].replace(0, np.nan) * 100
    ).round(2)

    # ── Leverage Metrics ────────────────────────────────────────
    df['debt_to_assets'] = (
        df['total_debt_mn'] / df['total_assets_mn'].replace(0, np.nan)
    ).round(4)

    df['fcf_margin_pct'] = (
        df['free_cash_flow_mn'] / df['revenue_mn'].replace(0, np.nan) * 100
    ).round(2)

    # ── Valuation Proxy (P/E using market cap) ──────────────────
    # EPS from DB; price ≈ market_cap_bn*1000 / shares (simplified)
    df['pe_proxy'] = (
        df['market_cap_bn'] * 1000 / df['eps'].replace(0, np.nan)
    ).round(2)

    # ── YoY Revenue Growth ──────────────────────────────────────
    df = df.sort_values(['ticker', 'fiscal_year'])
    df['revenue_yoy_growth'] = (
        df.groupby('ticker')['revenue_mn'].pct_change() * 100
    ).round(2)

    # ── 2-Year Revenue CAGR (2021→2023) ─────────────────────────
    pivot = df.pivot_table(
        index='ticker', columns='fiscal_year', values='revenue_mn'
    )
    if 2021 in pivot.columns and 2023 in pivot.columns:
        pivot['cagr_2yr'] = (
            (pivot[2023] / pivot[2021]) ** (1/2) - 1
        ).round(4) * 100

    df = df.merge(
        pivot[['cagr_2yr']].reset_index(),
        on='ticker', how='left'
    )

    # ── Export ───────────────────────────────────────────────────
    output_path = "data/processed/financial_metrics.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Financial metrics exported → {output_path}")
    print(f"   Shape: {df.shape[0]} rows × {df.shape[1]} columns")

    # Quick preview
    preview_cols = ['ticker','fiscal_year','gross_margin_pct',
                    'ebitda_margin_pct','net_margin_pct','cagr_2yr']
    print("\n📊 Sample Output (2023):")
    print(df[df['fiscal_year']==2023][preview_cols]
          .sort_values('net_margin_pct', ascending=False)
          .to_string(index=False))

    return df

if __name__ == "__main__":
    compute_metrics()