# python/sentiment_analysis.py
# Simulates news sentiment analysis for all 10 companies
# Uses NLTK VADER — purpose-built for financial text

import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from db_connection import get_connection
import random
from datetime import datetime, timedelta

# Download VADER lexicon (only needed once)
nltk.download('vader_lexicon', quiet=True)

# ── Simulated Financial News Headlines ──────────────────────
# In production: replace with NewsAPI or scraped headlines
HEADLINES = {
    'AAPL': [
        "Apple reports record iPhone sales driven by AI features",
        "Apple faces antitrust scrutiny over App Store policies",
        "Apple Vision Pro disappoints with slow adoption rate",
        "Apple expands renewable energy commitment to 100% globally",
        "Supply chain concerns emerge for Apple amid Taiwan tensions",
        "Apple Services revenue hits all-time high in Q4",
    ],
    'MSFT': [
        "Microsoft Copilot drives record Azure cloud revenue growth",
        "Microsoft acquires AI startup to bolster enterprise offerings",
        "Microsoft named top ESG technology company by MSCI",
        "Microsoft faces EU regulatory probe over Teams bundling",
        "Microsoft carbon negative target on track for 2030",
        "Microsoft enterprise AI adoption surpasses analyst expectations",
    ],
    'XOM': [
        "Exxon faces investor pressure over climate change strategy",
        "Exxon reports strong quarterly profits on high oil prices",
        "Exxon carbon capture project faces regulatory delays",
        "Exxon shareholders reject enhanced climate disclosure proposal",
        "Exxon accused of misleading public on climate risks",
        "Exxon increases dividend despite ESG criticism from funds",
    ],
    'NEE': [
        "NextEra Energy wins largest solar contract in US history",
        "NextEra raises clean energy investment target to $150bn",
        "NextEra named most sustainable utility by Dow Jones Index",
        "NextEra wind farm project approved in Midwest expansion",
        "NextEra partners with hydrogen storage technology startup",
        "NextEra beats earnings estimates on strong renewables demand",
    ],
    'JPM': [
        "JPMorgan increases sustainable finance commitment to $2.5 trillion",
        "JPMorgan faces criticism for continued fossil fuel financing",
        "JPMorgan AI trading platform reduces operational costs by 20%",
        "JPMorgan reports record investment banking fees in Q3",
        "JPMorgan CEO warns of economic headwinds in 2024 outlook",
        "JPMorgan launches green bond fund for institutional investors",
    ],
    'TSLA': [
        "Tesla Cybertruck production ramp exceeds initial forecasts",
        "Tesla faces union organizing efforts at Nevada gigafactory",
        "Tesla CEO compensation package rejected by shareholders again",
        "Tesla FSD technology achieves breakthrough in safety metrics",
        "Tesla cuts prices aggressively amid rising EV competition",
        "Tesla energy storage business grows 150% year over year",
    ],
    'JNJ': [
        "Johnson & Johnson talc settlement clears path for Kenvue spinoff",
        "JNJ oncology pipeline shows promising Phase 3 trial results",
        "JNJ raises dividend for 61st consecutive year",
        "JNJ faces new litigation over surgical mesh products",
        "JNJ MedTech division outperforms amid aging population trends",
        "JNJ named to Dow Jones Sustainability Index for 25th year",
    ],
    'AMZN': [
        "Amazon AWS revenue growth accelerates on AI infrastructure demand",
        "Amazon faces labor strike at multiple fulfillment centers",
        "Amazon antitrust case proceeds in federal court",
        "Amazon Prime membership crosses 200 million globally",
        "Amazon announces 100000 new renewable energy projects",
        "Amazon same-day delivery expansion drives market share gains",
    ],
    'CVX': [
        "Chevron Hess acquisition faces FTC regulatory challenge",
        "Chevron increases share buyback program to $75 billion",
        "Chevron faces criticism over slow energy transition progress",
        "Chevron reports strong free cash flow on oil price strength",
        "Chevron carbon capture investment doubled in 2023",
        "Chevron shareholders push for stronger climate commitments",
    ],
    'UL': [
        "Unilever sustainability brands outperform conventional portfolio",
        "Unilever CEO presents new growth strategy to investors",
        "Unilever divests ice cream unit to focus on core categories",
        "Unilever achieves plastic packaging reduction targets ahead of schedule",
        "Unilever raises prices successfully despite consumer pushback",
        "Unilever named global leader in sustainable sourcing practices",
    ],
}

def analyze_sentiment():
    sia = SentimentIntensityAnalyzer()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing sentiment data
    cursor.execute("DELETE FROM news_sentiment")
    conn.commit()

    results = []
    base_date = datetime(2023, 1, 1)

    print("🔍 Running sentiment analysis on financial headlines...\n")

    for ticker, headlines in HEADLINES.items():
        ticker_scores = []

        for i, headline in enumerate(headlines):
            # Get VADER sentiment scores
            scores = sia.polarity_scores(headline)
            compound = scores['compound']  # -1 to +1

            # Classify sentiment
            if compound >= 0.05:
                label = 'Positive'
            elif compound <= -0.05:
                label = 'Negative'
            else:
                label = 'Neutral'

            # Simulate a news date
            news_date = base_date + timedelta(days=random.randint(0, 364))

            # Insert into SQL
            cursor.execute("""
                INSERT INTO news_sentiment
                    (ticker, news_date, headline, sentiment_score,
                     sentiment_label, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                ticker,
                news_date.strftime('%Y-%m-%d'),
                headline,
                round(compound, 4),
                label,
                'Simulated-Financial-News'
            )

            ticker_scores.append(compound)
            results.append({
                'ticker': ticker,
                'headline': headline[:60] + '...',
                'compound_score': round(compound, 4),
                'label': label
            })

        avg_score = round(sum(ticker_scores) / len(ticker_scores), 4)
        print(f"  {ticker:6} | Avg Sentiment: {avg_score:+.4f} | "
              f"Headlines: {len(headlines)}")

    conn.commit()
    conn.close()

    # Export results
    df = pd.DataFrame(results)
    df.to_csv("data/processed/sentiment_scores.csv", index=False)
    print(f"\n✅ Sentiment data saved → data/processed/sentiment_scores.csv")
    print(f"   Total headlines analyzed: {len(results)}")

    return df

if __name__ == "__main__":
    analyze_sentiment()