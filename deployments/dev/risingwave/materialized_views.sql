-- =============================================================================
-- RisingWave Materialized Views for Technical Indicators
-- =============================================================================
-- This file creates:
-- 1. A SOURCE table that ingests candles from Kafka
-- 2. Materialized views for EMA, RSI, MACD
-- 3. A combined features view joining all indicators
-- 4. A SINK that publishes features back to Kafka
--
-- Run with: psql -h localhost -p 4566 -d dev -U root -f materialized_views.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Step 1: Create a SOURCE that reads from the Kafka "candles" topic
-- -----------------------------------------------------------------------------
-- CREATE SOURCE = RisingWave subscribes to the topic but doesn't store raw data.
-- We use this because we only need the computed features, not the raw candles.

CREATE SOURCE IF NOT EXISTS candles_source (
    pair VARCHAR,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    window_start_ms BIGINT,
    window_end_ms BIGINT
) WITH (
    connector = 'kafka',
    topic = 'candles',
    properties.bootstrap.server = 'kafka-0.kafka-headless.kafka.svc.cluster.local:9092',
    scan.startup.mode = 'earliest'
) FORMAT PLAIN ENCODE JSON;

-- -----------------------------------------------------------------------------
-- Step 2: Base materialized view — candles with row numbers for windowed calcs
-- -----------------------------------------------------------------------------
-- This adds a sequential row number per pair, ordered by window_start_ms.
-- Downstream views use this to reference "the last N candles."

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_candles_numbered AS
SELECT
    pair,
    open,
    high,
    low,
    close,
    volume,
    window_start_ms,
    window_end_ms,
    ROW_NUMBER() OVER (PARTITION BY pair ORDER BY window_start_ms) AS rn
FROM candles_source;

-- -----------------------------------------------------------------------------
-- Step 3: EMA (Exponential Moving Average) — 14-period
-- -----------------------------------------------------------------------------
-- EMA gives more weight to recent prices. It's used as:
-- - A trend indicator (price above EMA = bullish)
-- - Input to other indicators (MACD uses EMA-12 and EMA-26)
--
-- True EMA is recursive and hard in pure SQL. We approximate using a
-- weighted average over the last 14 candles, which is close enough for
-- feature engineering purposes.
--
-- Weight formula: k = 2 / (period + 1) = 2/15 ≈ 0.1333
-- Each candle gets weight: k * (1-k)^(distance_from_current)

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ema AS
SELECT
    c1.pair,
    c1.window_start_ms,
    c1.window_end_ms,
    c1.close AS current_close,
    -- EMA-14 approximation: weighted average of last 14 closes
    SUM(c2.close * POWER(0.8667, c1.rn - c2.rn) * 0.1333) /
        NULLIF(SUM(POWER(0.8667, c1.rn - c2.rn) * 0.1333), 0) AS ema_14
FROM mv_candles_numbered c1
JOIN mv_candles_numbered c2
    ON c1.pair = c2.pair
    AND c2.rn BETWEEN c1.rn - 13 AND c1.rn
GROUP BY c1.pair, c1.window_start_ms, c1.window_end_ms, c1.close, c1.rn;

-- -----------------------------------------------------------------------------
-- Step 4: RSI (Relative Strength Index) — 14-period
-- -----------------------------------------------------------------------------
-- RSI measures momentum on a scale of 0-100:
-- - RSI > 70 → overbought (price might drop)
-- - RSI < 30 → oversold (price might rise)
--
-- Formula: RSI = 100 - (100 / (1 + RS))
-- where RS = average_gain / average_loss over 14 periods

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_price_changes AS
SELECT
    c1.pair,
    c1.window_start_ms,
    c1.window_end_ms,
    c1.close,
    c1.rn,
    c1.close - c2.close AS price_change
FROM mv_candles_numbered c1
JOIN mv_candles_numbered c2
    ON c1.pair = c2.pair
    AND c2.rn = c1.rn - 1
WHERE c1.rn > 1;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_rsi AS
SELECT
    pc.pair,
    pc.window_start_ms,
    pc.window_end_ms,
    pc.close AS current_close,
    -- Average gain over last 14 periods
    AVG(CASE WHEN pc2.price_change > 0 THEN pc2.price_change ELSE 0 END) AS avg_gain,
    -- Average loss over last 14 periods (absolute value)
    AVG(CASE WHEN pc2.price_change < 0 THEN ABS(pc2.price_change) ELSE 0 END) AS avg_loss,
    -- RSI calculation
    CASE
        WHEN AVG(CASE WHEN pc2.price_change < 0 THEN ABS(pc2.price_change) ELSE 0 END) = 0 THEN 100.0
        ELSE 100.0 - (100.0 / (1.0 + (
            AVG(CASE WHEN pc2.price_change > 0 THEN pc2.price_change ELSE 0 END) /
            NULLIF(AVG(CASE WHEN pc2.price_change < 0 THEN ABS(pc2.price_change) ELSE 0 END), 0)
        )))
    END AS rsi_14
FROM mv_price_changes pc
JOIN mv_price_changes pc2
    ON pc.pair = pc2.pair
    AND pc2.rn BETWEEN pc.rn - 13 AND pc.rn
GROUP BY pc.pair, pc.window_start_ms, pc.window_end_ms, pc.close, pc.rn;

-- -----------------------------------------------------------------------------
-- Step 5: MACD (Moving Average Convergence Divergence)
-- -----------------------------------------------------------------------------
-- MACD = EMA-12 - EMA-26
-- Signal line = EMA-9 of MACD (we approximate with simple average of last 9 MACDs)
-- Histogram = MACD - Signal
--
-- Interpretation:
-- - MACD > Signal → bullish momentum
-- - MACD < Signal → bearish momentum
-- - Histogram growing → trend strengthening

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ema_components AS
SELECT
    c1.pair,
    c1.window_start_ms,
    c1.window_end_ms,
    c1.close AS current_close,
    c1.rn,
    -- EMA-12 approximation (k = 2/13 ≈ 0.1538)
    SUM(c2.close * POWER(0.8462, c1.rn - c2.rn) * 0.1538) /
        NULLIF(SUM(POWER(0.8462, c1.rn - c2.rn) * 0.1538), 0) AS ema_12,
    -- EMA-26 approximation (k = 2/27 ≈ 0.0741)
    SUM(c3.close * POWER(0.9259, c1.rn - c3.rn) * 0.0741) /
        NULLIF(SUM(POWER(0.9259, c1.rn - c3.rn) * 0.0741), 0) AS ema_26
FROM mv_candles_numbered c1
JOIN mv_candles_numbered c2
    ON c1.pair = c2.pair
    AND c2.rn BETWEEN c1.rn - 11 AND c1.rn
JOIN mv_candles_numbered c3
    ON c1.pair = c3.pair
    AND c3.rn BETWEEN c1.rn - 25 AND c1.rn
WHERE c1.rn >= 26
GROUP BY c1.pair, c1.window_start_ms, c1.window_end_ms, c1.close, c1.rn;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_macd AS
SELECT
    e1.pair,
    e1.window_start_ms,
    e1.window_end_ms,
    e1.current_close,
    e1.ema_12,
    e1.ema_26,
    e1.ema_12 - e1.ema_26 AS macd_line,
    -- Signal line: average of last 9 MACD values
    AVG(e2.ema_12 - e2.ema_26) AS macd_signal,
    -- Histogram
    (e1.ema_12 - e1.ema_26) - AVG(e2.ema_12 - e2.ema_26) AS macd_histogram
FROM mv_ema_components e1
JOIN mv_ema_components e2
    ON e1.pair = e2.pair
    AND e2.rn BETWEEN e1.rn - 8 AND e1.rn
GROUP BY e1.pair, e1.window_start_ms, e1.window_end_ms, e1.current_close,
         e1.ema_12, e1.ema_26, e1.rn;

-- -----------------------------------------------------------------------------
-- Step 6: Combined features view — single source of truth for ML model
-- -----------------------------------------------------------------------------
-- This joins all indicators into one row per candle per pair.
-- The predictor service will query this view for both training and inference.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_features AS
SELECT
    e.pair,
    e.window_start_ms,
    e.window_end_ms,
    e.current_close,
    e.ema_14,
    r.rsi_14,
    m.macd_line,
    m.macd_signal,
    m.macd_histogram
FROM mv_ema e
LEFT JOIN mv_rsi r
    ON e.pair = r.pair AND e.window_start_ms = r.window_start_ms
LEFT JOIN mv_macd m
    ON e.pair = m.pair AND e.window_start_ms = m.window_start_ms;

-- -----------------------------------------------------------------------------
-- Step 7: Sink features to Kafka "features" topic
-- -----------------------------------------------------------------------------
-- This allows downstream services (predictor) to consume features from Kafka
-- instead of querying RisingWave directly — decouples the systems.

CREATE SINK IF NOT EXISTS sink_features FROM mv_features WITH (
    connector = 'kafka',
    topic = 'features',
    properties.bootstrap.server = 'kafka-0.kafka-headless.kafka.svc.cluster.local:9092'
) FORMAT PLAIN ENCODE JSON (
    force_append_only = 'true'
);
