# python/export_master.py
# Merges all processed data into one master CSV for Power BI

import pandas as pd
from db_connection import run_query

def create_master_dataset():
    # Load from SQL
    companies = run_query("SELECT * FROM companies")
    financials = run_query("SELECT * FROM financials")
    esg        = run_query("SELECT * FROM esg_scores")

    # Load processed metrics
    metrics = pd.read_csv("data/processed/financial_metrics.csv")
    tiers   = pd.read_csv("data/processed/esg_investment_tiers.csv")

    # ── Merge all layers ─────────────────────────────────────────
    master = financials.merge(companies, on='ticker', how='left')
    master = master.merge(
        esg[['ticker','score_year','environmental_score',
             'social_score','governance_score',
             'composite_esg_score','esg_rating','carbon_intensity']],
        left_on=['ticker','fiscal_year'],
        right_on=['ticker','score_year'],
        how='left'
    )
    master = master.merge(
        metrics[['ticker','fiscal_year','gross_margin_pct',
                 'ebitda_margin_pct','net_margin_pct',
                 'revenue_yoy_growth','cagr_2yr']],
        on=['ticker','fiscal_year'],
        how='left'
    )
    master = master.merge(
        tiers[['ticker','weighted_esg_score',
               'esg_momentum','investment_tier']],
        on='ticker',
        how='left'
    )

    # ── Clean up duplicate columns ───────────────────────────────
    master = master.drop(columns=['score_year','created_at_x',
                                  'created_at_y'], errors='ignore')

    # ── Export ───────────────────────────────────────────────────
    master.to_csv("data/processed/master_dataset.csv", index=False)
    print(f"✅ Master dataset exported → data/processed/master_dataset.csv")
    print(f"   Shape: {master.shape[0]} rows × {master.shape[1]} columns")
    print(f"\n📋 Columns: {list(master.columns)}")

    return master

if __name__ == "__main__":
    create_master_dataset()