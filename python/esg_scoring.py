# python/esg_scoring.py
# Builds a weighted ESG composite score and investment tier
# Weights mirror MSCI ESG methodology

import pandas as pd
import numpy as np
from db_connection import run_query

# ── ESG Sub-score Weights ────────────────────────────────────────
# Environmental weighted highest for this model
WEIGHTS = {
    'environmental_score': 0.40,
    'social_score':        0.30,
    'governance_score':    0.30
}

def assign_rating(score):
    """Convert numeric score to letter rating (MSCI-style)."""
    if   score >= 85: return 'AAA'
    elif score >= 75: return 'AA'
    elif score >= 65: return 'A'
    elif score >= 55: return 'BBB'
    elif score >= 45: return 'BB'
    elif score >= 35: return 'B'
    else:             return 'CCC'

def assign_investment_tier(esg_score, net_margin, cagr):
    """
    Simple rule-based investment recommendation.
    Combines ESG quality with financial performance.
    """
    financial_score = (
        (min(max(net_margin, -10), 35) / 35) * 50 +
        (min(max(cagr, -5), 45) / 45) * 50
    )
    combined = esg_score * 0.5 + financial_score * 0.5

    if   combined >= 70: return 'Strong Buy'
    elif combined >= 55: return 'Buy'
    elif combined >= 42: return 'Hold'
    elif combined >= 30: return 'Underperform'
    else:                return 'Sell'

def compute_esg_scores():
    # Load ESG raw scores
    esg = run_query("""
        SELECT ticker, score_year,
               environmental_score, social_score,
               governance_score, carbon_intensity
        FROM esg_scores
    """)

    # Load 2023 financials for investment tier
    fin = run_query("""
        SELECT ticker,
               ROUND(net_income_mn/NULLIF(revenue_mn,0)*100, 2) AS net_margin,
               revenue_mn
        FROM financials
        WHERE fiscal_year = 2023
    """)

    # ── Recompute weighted composite ────────────────────────────
    esg['weighted_esg_score'] = (
        esg['environmental_score'] * WEIGHTS['environmental_score'] +
        esg['social_score']        * WEIGHTS['social_score']        +
        esg['governance_score']    * WEIGHTS['governance_score']
    ).round(2)

    # ── Normalise carbon intensity (lower = better) ──────────────
    max_ci = esg['carbon_intensity'].max()
    esg['carbon_score'] = (
        (1 - esg['carbon_intensity'] / max_ci) * 100
    ).round(2)

    # ── ESG Momentum (YoY change) ────────────────────────────────
    esg = esg.sort_values(['ticker','score_year'])
    esg['esg_momentum'] = (
        esg.groupby('ticker')['weighted_esg_score'].diff()
    ).round(2)

    # ── Letter Rating ────────────────────────────────────────────
    esg['calculated_rating'] = esg['weighted_esg_score'].apply(assign_rating)

    # ── CAGR from financials (simplified: load from metrics CSV) ─
    try:
        metrics = pd.read_csv("data/processed/financial_metrics.csv")
        cagr_map = metrics[metrics['fiscal_year']==2023]\
                   .set_index('ticker')['cagr_2yr'].to_dict()
    except:
        cagr_map = {}

    # ── Investment Tier (2023 only) ──────────────────────────────
    fin_map = fin.set_index('ticker')['net_margin'].to_dict()

    esg_2023 = esg[esg['score_year']==2023].copy()
    esg_2023['investment_tier'] = esg_2023.apply(
        lambda r: assign_investment_tier(
            r['weighted_esg_score'],
            fin_map.get(r['ticker'], 0),
            cagr_map.get(r['ticker'], 0)
        ), axis=1
    )

    # ── Export full ESG data ─────────────────────────────────────
    esg.to_csv("data/processed/esg_scores_processed.csv", index=False)
    esg_2023.to_csv("data/processed/esg_investment_tiers.csv", index=False)

    print("✅ ESG scores exported → data/processed/esg_scores_processed.csv")
    print("✅ Investment tiers exported → data/processed/esg_investment_tiers.csv")
    print("\n📊 2023 ESG Investment Tiers:")
    print(esg_2023[['ticker','weighted_esg_score',
                    'calculated_rating','esg_momentum',
                    'investment_tier']]
          .sort_values('weighted_esg_score', ascending=False)
          .to_string(index=False))

    return esg, esg_2023

if __name__ == "__main__":
    compute_esg_scores()