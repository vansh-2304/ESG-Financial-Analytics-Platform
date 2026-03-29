# python/ai_recommendation.py
# Combines ESG score + Financial metrics + News sentiment
# into a single AI-driven investment recommendation score

import pandas as pd
import numpy as np
from db_connection import run_query

def normalize(series, invert=False):
    """Normalize a series to 0-100 scale."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([50] * len(series), index=series.index)
    normalized = (series - mn) / (mx - mn) * 100
    return (100 - normalized) if invert else normalized

def compute_ai_score():
    print("🤖 AI Investment Recommendation Engine")
    print("=" * 55)

    # ── Load all data sources ────────────────────────────────
    financials = run_query("""
        SELECT ticker,
            ROUND(net_income_mn/NULLIF(revenue_mn,0)*100,2)
                AS net_margin,
            ROUND(ebitda_mn/NULLIF(revenue_mn,0)*100,2)
                AS ebitda_margin,
            free_cash_flow_mn,
            roe
        FROM financials
        WHERE fiscal_year = 2023
    """)

    esg = run_query("""
        SELECT ticker, composite_esg_score,
               environmental_score, carbon_intensity
        FROM esg_scores
        WHERE score_year = 2023
    """)

    # Load sentiment averages
    sentiment = run_query("""
        SELECT ticker,
               AVG(sentiment_score) AS avg_sentiment,
               COUNT(*) AS headline_count
        FROM news_sentiment
        GROUP BY ticker
    """)

    # Load predictions
    try:
        predictions = pd.read_csv(
            "data/processed/esg_predictions_2024.csv"
        )
    except:
        predictions = pd.DataFrame(
            columns=['ticker','predicted_esg_2024','annual_esg_trend']
        )

    # ── Merge all data ───────────────────────────────────────
    df = financials.merge(esg, on='ticker')
    df = df.merge(sentiment, on='ticker', how='left')
    df = df.merge(
        predictions[['ticker','predicted_esg_2024',
                     'annual_esg_trend']],
        on='ticker', how='left'
    )
    df['avg_sentiment'] = df['avg_sentiment'].fillna(0)

    # ── PILLAR 1: Financial Score (35% weight) ───────────────
    df['fin_margin_score']  = normalize(df['net_margin'])
    df['fin_ebitda_score']  = normalize(df['ebitda_margin'])
    df['fin_fcf_score']     = normalize(df['free_cash_flow_mn'])
    df['fin_roe_score']     = normalize(df['roe'])

    df['financial_pillar'] = (
        df['fin_margin_score']  * 0.35 +
        df['fin_ebitda_score']  * 0.25 +
        df['fin_fcf_score']     * 0.25 +
        df['fin_roe_score']     * 0.15
    ).round(2)

    # ── PILLAR 2: ESG Score (40% weight) ────────────────────
    df['esg_current_score'] = normalize(df['composite_esg_score'])
    df['esg_carbon_score']  = normalize(
        df['carbon_intensity'], invert=True
    )
    df['esg_future_score']  = normalize(
        df['predicted_esg_2024'].fillna(df['composite_esg_score'])
    )
    df['esg_trend_score']   = normalize(
        df['annual_esg_trend'].fillna(0)
    )

    df['esg_pillar'] = (
        df['esg_current_score'] * 0.40 +
        df['esg_carbon_score']  * 0.25 +
        df['esg_future_score']  * 0.20 +
        df['esg_trend_score']   * 0.15
    ).round(2)

    # ── PILLAR 3: Sentiment Score (25% weight) ───────────────
    df['sentiment_normalized'] = (
        (df['avg_sentiment'] + 1) / 2 * 100
    ).round(2)

    df['sentiment_pillar'] = df['sentiment_normalized']

    # ── FINAL AI COMPOSITE SCORE ─────────────────────────────
    df['ai_composite_score'] = (
        df['financial_pillar'] * 0.35 +
        df['esg_pillar']       * 0.40 +
        df['sentiment_pillar'] * 0.25
    ).round(2)

    # ── AI Recommendation ────────────────────────────────────
    def ai_recommend(score):
        if   score >= 72: return 'Strong Buy'
        elif score >= 58: return 'Buy'
        elif score >= 44: return 'Hold'
        elif score >= 30: return 'Underperform'
        else:             return 'Sell'

    df['ai_recommendation'] = df['ai_composite_score'].apply(
        ai_recommend
    )

    # ── Confidence Level ─────────────────────────────────────
    def confidence(score):
        if score >= 80 or score <= 20: return 'High'
        elif score >= 65 or score <= 35: return 'Medium'
        else: return 'Low'

    df['confidence'] = df['ai_composite_score'].apply(confidence)

    # ── Output columns ───────────────────────────────────────
    output = df[[
        'ticker', 'financial_pillar', 'esg_pillar',
        'sentiment_pillar', 'ai_composite_score',
        'ai_recommendation', 'confidence',
        'avg_sentiment', 'predicted_esg_2024'
    ]].sort_values('ai_composite_score', ascending=False)

    # ── Export ───────────────────────────────────────────────
    output.to_csv(
        "data/processed/ai_recommendations.csv", index=False
    )

    # ── Print Results ────────────────────────────────────────
    print(f"\n{'Ticker':<7}{'Fin':>6}{'ESG':>6}"
          f"{'Sent':>6}{'AI Score':>10}"
          f"{'Recommendation':<16}{'Conf'}")
    print("-" * 60)

    for _, r in output.iterrows():
        print(
            f"{r['ticker']:<7}"
            f"{r['financial_pillar']:>6.1f}"
            f"{r['esg_pillar']:>6.1f}"
            f"{r['sentiment_pillar']:>6.1f}"
            f"{r['ai_composite_score']:>10.1f}"
            f"  {r['ai_recommendation']:<16}"
            f"{r['confidence']}"
        )

    print(f"\n✅ AI recommendations → "
          f"data/processed/ai_recommendations.csv")

    return output

if __name__ == "__main__":
    compute_ai_score()