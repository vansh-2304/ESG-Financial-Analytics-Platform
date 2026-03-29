USE ESGFinancialPlatform;
GO

-- ============================================================
-- SECTION 1: VALIDATION QUERIES
-- ============================================================

-- Query V1: Row counts in all tables
SELECT 'companies'       AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL
SELECT 'financials',     COUNT(*) FROM financials
UNION ALL
SELECT 'stock_prices',   COUNT(*) FROM stock_prices
UNION ALL
SELECT 'esg_scores',     COUNT(*) FROM esg_scores
UNION ALL
SELECT 'news_sentiment', COUNT(*) FROM news_sentiment;
GO

-- Query V2: ESG vs Financial snapshot
SELECT
    c.ticker, c.company_name, c.sector, f.fiscal_year,
    f.revenue_mn, f.net_income_mn,
    ROUND((f.net_income_mn/NULLIF(f.revenue_mn,0))*100,2)
        AS net_margin_pct,
    e.composite_esg_score, e.esg_rating, e.carbon_intensity
FROM companies c
JOIN financials f ON c.ticker = f.ticker
JOIN esg_scores e ON c.ticker = e.ticker
    AND f.fiscal_year = e.score_year
WHERE f.fiscal_year = 2023
ORDER BY e.composite_esg_score DESC;
GO

-- Query V3: Revenue growth 2021 to 2023
SELECT
    ticker,
    MAX(CASE WHEN fiscal_year=2021 THEN revenue_mn END) AS rev_2021,
    MAX(CASE WHEN fiscal_year=2023 THEN revenue_mn END) AS rev_2023,
    ROUND(
        (MAX(CASE WHEN fiscal_year=2023 THEN revenue_mn END) -
         MAX(CASE WHEN fiscal_year=2021 THEN revenue_mn END)) /
         NULLIF(MAX(CASE WHEN fiscal_year=2021
             THEN revenue_mn END),0)*100
    ,2) AS revenue_growth_2yr_pct
FROM financials
GROUP BY ticker
ORDER BY revenue_growth_2yr_pct DESC;
GO

-- ============================================================
-- SECTION 2: ANALYTICAL QUERIES
-- ============================================================

-- Query A1: ESG Leaders vs Laggards Comparison
SELECT
    CASE WHEN e.esg_rating IN ('AAA','AA')
         THEN 'ESG Leader'
         ELSE 'ESG Laggard'
    END AS esg_group,
    COUNT(DISTINCT c.ticker)        AS company_count,
    ROUND(AVG(e.composite_esg_score),2) AS avg_esg_score,
    ROUND(AVG(f.net_income_mn/
        NULLIF(f.revenue_mn,0)*100),2)  AS avg_net_margin,
    ROUND(AVG(e.carbon_intensity),2)    AS avg_carbon_intensity
FROM companies c
JOIN financials f ON c.ticker = f.ticker
JOIN esg_scores e ON c.ticker = e.ticker
    AND f.fiscal_year = e.score_year
WHERE f.fiscal_year = 2023
GROUP BY
    CASE WHEN e.esg_rating IN ('AAA','AA')
         THEN 'ESG Leader'
         ELSE 'ESG Laggard'
    END;
GO

-- Query A2: Sentiment vs ESG Analysis
SELECT
    c.ticker, c.company_name,
    e.composite_esg_score, e.esg_rating,
    ROUND(AVG(n.sentiment_score),4) AS avg_sentiment,
    COUNT(n.id)                     AS headline_count
FROM companies c
JOIN esg_scores e ON c.ticker = e.ticker
    AND e.score_year = 2023
LEFT JOIN news_sentiment n ON c.ticker = n.ticker
GROUP BY c.ticker, c.company_name,
         e.composite_esg_score, e.esg_rating
ORDER BY avg_sentiment DESC;
GO

-- Query A3: Stock Price Performance Summary
SELECT
    ticker,
    MIN(close_price)                    AS min_price,
    MAX(close_price)                    AS max_price,
    ROUND(AVG(close_price),2)           AS avg_price,
    ROUND((MAX(close_price)-MIN(close_price))/
        NULLIF(MIN(close_price),0)*100,2) AS price_range_pct
FROM stock_prices
GROUP BY ticker
ORDER BY price_range_pct DESC;
GO

-- Query A4: Full ESG + Financial + Sentiment Dashboard
SELECT
    c.ticker, c.company_name, c.sector,
    e.composite_esg_score, e.esg_rating,
    e.carbon_intensity,
    ROUND(f.net_income_mn/
        NULLIF(f.revenue_mn,0)*100,2)   AS net_margin_pct,
    ROUND(f.ebitda_mn/
        NULLIF(f.revenue_mn,0)*100,2)   AS ebitda_margin_pct,
    f.free_cash_flow_mn,
    ROUND(AVG(n.sentiment_score),4)     AS avg_sentiment
FROM companies c
JOIN financials f  ON c.ticker = f.ticker
JOIN esg_scores e  ON c.ticker = e.ticker
    AND f.fiscal_year = e.score_year
LEFT JOIN news_sentiment n ON c.ticker = n.ticker
WHERE f.fiscal_year = 2023
GROUP BY
    c.ticker, c.company_name, c.sector,
    e.composite_esg_score, e.esg_rating,
    e.carbon_intensity, f.net_income_mn,
    f.revenue_mn, f.ebitda_mn, f.free_cash_flow_mn
ORDER BY e.composite_esg_score DESC;
GO

-- Query A5: ESG Trend Analysis 2021-2023
SELECT
    ticker,
    MAX(CASE WHEN score_year=2021
        THEN composite_esg_score END) AS esg_2021,
    MAX(CASE WHEN score_year=2022
        THEN composite_esg_score END) AS esg_2022,
    MAX(CASE WHEN score_year=2023
        THEN composite_esg_score END) AS esg_2023,
    ROUND(
        MAX(CASE WHEN score_year=2023
            THEN composite_esg_score END) -
        MAX(CASE WHEN score_year=2021
            THEN composite_esg_score END)
    ,2) AS esg_improvement_2yr
FROM esg_scores
GROUP BY ticker
ORDER BY esg_improvement_2yr DESC;
GO