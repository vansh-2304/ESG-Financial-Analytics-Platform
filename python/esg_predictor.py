# python/esg_predictor.py
# Predicts 2024 ESG scores using Linear Regression
# on 2021-2023 historical ESG data

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
from db_connection import run_query

def predict_esg_scores():
    # Load historical ESG data
    esg = run_query("""
        SELECT ticker, score_year,
               environmental_score, social_score,
               governance_score, composite_esg_score
        FROM esg_scores
        ORDER BY ticker, score_year
    """)

    print("📈 ESG Score Prediction Model (Linear Regression)")
    print("=" * 55)

    predictions = []

    for ticker in esg['ticker'].unique():
        df = esg[esg['ticker'] == ticker].copy()

        # Feature: year (2021, 2022, 2023)
        X = df[['score_year']]
        
        for score_col in ['environmental_score', 'social_score',
                          'governance_score', 'composite_esg_score']:

            y = df[score_col]

            # Fit linear regression
            model = LinearRegression()
            model.fit(X, y)

            # Predict 2024
            pred_2024 = model.predict([[2024]])[0]

            # Model quality
            y_pred = model.predict(X)
            r2  = r2_score(y, y_pred)
            mae = mean_absolute_error(y, y_pred)

            predictions.append({
                'ticker':       ticker,
                'score_type':   score_col,
                'pred_2024':    round(pred_2024, 2),
                'r2_score':     round(r2, 4),
                'mae':          round(mae, 4),
                'annual_trend': round(model.coef_[0], 3)
            })

    pred_df = pd.DataFrame(predictions)

    # ── Pivot to wide format ─────────────────────────────────
    composite = pred_df[
        pred_df['score_type'] == 'composite_esg_score'
    ][['ticker','pred_2024','annual_trend','r2_score']].copy()

    composite.columns = [
        'ticker', 'predicted_esg_2024',
        'annual_esg_trend', 'model_r2'
    ]

    # ── Classify trend ───────────────────────────────────────
    composite['trend_label'] = composite['annual_esg_trend'].apply(
        lambda x: 'Improving ↑' if x > 1.5
                  else ('Stable →' if x >= 0.5
                  else 'Declining ↓')
    )

    # ── Export ───────────────────────────────────────────────
    composite.to_csv(
        "data/processed/esg_predictions_2024.csv", index=False
    )
    pred_df.to_csv(
        "data/processed/esg_predictions_full.csv", index=False
    )

    print(f"\n{'Ticker':<8} {'2023 Score':>10} "
          f"{'2024 Pred':>10} {'Trend':>8} {'Label':<15}")
    print("-" * 55)

    # Load 2023 actuals for comparison
    actuals = run_query("""
        SELECT ticker, composite_esg_score
        FROM esg_scores WHERE score_year = 2023
    """).set_index('ticker')['composite_esg_score'].to_dict()

    for _, row in composite.sort_values(
            'predicted_esg_2024', ascending=False).iterrows():
        actual = actuals.get(row['ticker'], 0)
        print(f"{row['ticker']:<8} {actual:>10.1f} "
              f"{row['predicted_esg_2024']:>10.2f} "
              f"{row['annual_esg_trend']:>+8.2f} "
              f"{row['trend_label']:<15}")

    print(f"\n✅ Predictions exported → "
          f"data/processed/esg_predictions_2024.csv")

    return composite

if __name__ == "__main__":
    predict_esg_scores()