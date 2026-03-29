-- Create the project database
CREATE DATABASE ESGFinancialPlatform;
GO

-- Switch to it
USE ESGFinancialPlatform;
GO
---------Create All 5 Tables----------
USE ESGFinancialPlatform;
GO

-- ============================================================
-- TABLE 1: COMPANIES (Master Reference Table)
-- ============================================================
CREATE TABLE companies (
    ticker          VARCHAR(10)     PRIMARY KEY,
    company_name    VARCHAR(100)    NOT NULL,
    sector          VARCHAR(50)     NOT NULL,
    industry        VARCHAR(100),
    country         VARCHAR(50)     DEFAULT 'USA',
    market_cap_bn   DECIMAL(10,2),  -- in billions USD
    created_at      DATETIME        DEFAULT GETDATE()
);
GO

-- ============================================================
-- TABLE 2: FINANCIALS (Annual Income Statement Data)
-- ============================================================
CREATE TABLE financials (
    id                  INT             PRIMARY KEY IDENTITY(1,1),
    ticker              VARCHAR(10)     NOT NULL,
    fiscal_year         INT             NOT NULL,
    revenue_mn          DECIMAL(15,2),  -- in millions USD
    gross_profit_mn     DECIMAL(15,2),
    ebitda_mn           DECIMAL(15,2),
    net_income_mn       DECIMAL(15,2),
    eps                 DECIMAL(10,4),  -- earnings per share
    total_assets_mn     DECIMAL(15,2),
    total_debt_mn       DECIMAL(15,2),
    free_cash_flow_mn   DECIMAL(15,2),
    roe                 DECIMAL(8,4),   -- return on equity (%)
    created_at          DATETIME        DEFAULT GETDATE(),

    CONSTRAINT fk_financials_ticker
        FOREIGN KEY (ticker) REFERENCES companies(ticker),
    CONSTRAINT uq_financials
        UNIQUE (ticker, fiscal_year)
);
GO

-- ============================================================
-- TABLE 3: STOCK PRICES (Daily OHLCV Data)
-- ============================================================
CREATE TABLE stock_prices (
    id              INT             PRIMARY KEY IDENTITY(1,1),
    ticker          VARCHAR(10)     NOT NULL,
    price_date      DATE            NOT NULL,
    open_price      DECIMAL(10,4),
    high_price      DECIMAL(10,4),
    low_price       DECIMAL(10,4),
    close_price     DECIMAL(10,4),
    volume          BIGINT,
    adj_close       DECIMAL(10,4),  -- adjusted for splits/dividends
    created_at      DATETIME        DEFAULT GETDATE(),

    CONSTRAINT fk_prices_ticker
        FOREIGN KEY (ticker) REFERENCES companies(ticker),
    CONSTRAINT uq_stock_prices
        UNIQUE (ticker, price_date)
);
GO

-- ============================================================
-- TABLE 4: ESG SCORES (Annual ESG Ratings)
-- ============================================================
CREATE TABLE esg_scores (
    id                      INT             PRIMARY KEY IDENTITY(1,1),
    ticker                  VARCHAR(10)     NOT NULL,
    score_year              INT             NOT NULL,
    environmental_score     DECIMAL(5,2),   -- 0 to 100
    social_score            DECIMAL(5,2),   -- 0 to 100
    governance_score        DECIMAL(5,2),   -- 0 to 100
    composite_esg_score     DECIMAL(5,2),   -- weighted average
    esg_rating              VARCHAR(5),     -- AAA, AA, A, BBB, BB, B, CCC
    carbon_intensity        DECIMAL(10,4),  -- tonnes CO2 per $mn revenue
    data_source             VARCHAR(50)     DEFAULT 'Simulated-MSCI',
    created_at              DATETIME        DEFAULT GETDATE(),

    CONSTRAINT fk_esg_ticker
        FOREIGN KEY (ticker) REFERENCES companies(ticker),
    CONSTRAINT uq_esg_scores
        UNIQUE (ticker, score_year)
);
GO

-- ============================================================
-- TABLE 5: NEWS SENTIMENT (For AI/NLP Stage)
-- ============================================================
CREATE TABLE news_sentiment (
    id                  INT             PRIMARY KEY IDENTITY(1,1),
    ticker              VARCHAR(10)     NOT NULL,
    news_date           DATE            NOT NULL,
    headline            NVARCHAR(500),
    sentiment_score     DECIMAL(5,4),   -- -1.0 (negative) to +1.0 (positive)
    sentiment_label     VARCHAR(10),    -- Positive / Negative / Neutral
    source              VARCHAR(100),
    created_at          DATETIME        DEFAULT GETDATE(),

    CONSTRAINT fk_sentiment_ticker
        FOREIGN KEY (ticker) REFERENCES companies(ticker)
);
GO