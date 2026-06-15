"""Entry point for the technical_indicators service.

This service:
1. Consumes OHLCV candles from the "candles" Kafka topic
2. Computes technical indicators (EMA-14, RSI-14, MACD) using stateful processing
3. Produces feature rows to the "features" Kafka topic

This is a complementary path to the RisingWave SQL-based feature computation.
Both produce to the same "features" topic, demonstrating two approaches:
- RisingWave: streaming SQL (good for standard aggregations)
- This service: Python (good for complex/custom feature logic)

In production, you'd typically pick ONE approach. Here we implement both for learning.
When RisingWave is running with its own sink to "features", this service can be
stopped to avoid duplicate features. Or you can run only this service if RisingWave
is not deployed.

Run with: uv run python -m technical_indicators
"""

from collections import deque

from loguru import logger
from quixstreams import Application

from technical_indicators.config import settings
from technical_indicators.logging import setup_logging


def compute_ema(prices: list[float], period: int) -> float | None:
    """Compute Exponential Moving Average for the given period.

    EMA gives exponentially more weight to recent prices.
    Formula: EMA_t = price_t * k + EMA_(t-1) * (1 - k)
    where k = 2 / (period + 1)
    """
    if len(prices) < period:
        return None

    k = 2.0 / (period + 1)
    # Seed with SMA of first `period` prices
    ema = sum(prices[:period]) / period
    # Then apply EMA formula for remaining prices
    for price in prices[period:]:
        ema = price * k + ema * (1 - k)
    return ema


def compute_rsi(prices: list[float], period: int) -> float | None:
    """Compute Relative Strength Index.

    RSI = 100 - (100 / (1 + RS))
    where RS = avg_gain / avg_loss over `period` periods.
    RSI ranges from 0-100:
      > 70 = overbought
      < 30 = oversold
    """
    if len(prices) < period + 1:
        return None

    # Calculate price changes
    changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    # Take only the last `period` changes
    recent_changes = changes[-period:]

    gains = [c for c in recent_changes if c > 0]
    losses = [-c for c in recent_changes if c < 0]

    avg_gain = sum(gains) / period if gains else 0.0
    avg_loss = sum(losses) / period if losses else 0.0

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_macd(
    prices: list[float],
    short_period: int = 12,
    long_period: int = 26,
    signal_period: int = 9,
) -> dict | None:
    """Compute MACD (Moving Average Convergence Divergence).

    MACD line = EMA(short) - EMA(long)
    Signal line = EMA(signal) of MACD line
    Histogram = MACD - Signal

    Needs at least long_period + signal_period - 1 data points.
    """
    if len(prices) < long_period + signal_period - 1:
        return None

    # Compute MACD line for the last signal_period points
    macd_values = []
    for i in range(signal_period):
        end_idx = len(prices) - signal_period + i + 1
        subset = prices[:end_idx]
        ema_short = compute_ema(subset, short_period)
        ema_long = compute_ema(subset, long_period)
        if ema_short is not None and ema_long is not None:
            macd_values.append(ema_short - ema_long)

    if len(macd_values) < signal_period:
        return None

    # Signal line = SMA of last signal_period MACD values (simplified)
    signal = sum(macd_values) / len(macd_values)
    macd_line = macd_values[-1]

    return {
        "macd_line": macd_line,
        "macd_signal": signal,
        "macd_histogram": macd_line - signal,
    }


# State: keep a rolling window of close prices per pair
# We need at least 26 + 9 - 1 = 34 candles for MACD
MAX_HISTORY = 50
price_history: dict[str, deque] = {}


def process_candle(candle: dict) -> dict | None:
    """Process a single candle and compute all technical indicators.

    Accumulates close prices in memory per pair. Once enough history
    is available, computes and returns a feature row.
    """
    pair = candle["pair"]
    close = candle["close"]

    # Initialize history for this pair if needed
    if pair not in price_history:
        price_history[pair] = deque(maxlen=MAX_HISTORY)

    price_history[pair].append(close)
    prices = list(price_history[pair])

    # Need minimum history before computing indicators
    min_required = settings.ema_long_period + settings.macd_signal_period - 1
    if len(prices) < min_required:
        logger.debug(f"Accumulating history for {pair}: {len(prices)}/{min_required} candles")
        return None

    # Compute all indicators
    ema_14 = compute_ema(prices, 14)
    rsi_14 = compute_rsi(prices, settings.rsi_period)
    macd = compute_macd(
        prices,
        settings.ema_short_period,
        settings.ema_long_period,
        settings.macd_signal_period,
    )

    if ema_14 is None or rsi_14 is None or macd is None:
        return None

    return {
        "pair": pair,
        "window_start_ms": candle["window_start_ms"],
        "window_end_ms": candle["window_end_ms"],
        "current_close": close,
        "ema_14": round(ema_14, 2),
        "rsi_14": round(rsi_14, 2),
        "macd_line": round(macd["macd_line"], 4),
        "macd_signal": round(macd["macd_signal"], 4),
        "macd_histogram": round(macd["macd_histogram"], 4),
    }


def main() -> None:
    """Set up logging, configure the Quixstreams app, and run the pipeline."""
    setup_logging()

    logger.info("Starting technical_indicators service")
    logger.info(f"  Input topic:  {settings.kafka_input_topic}")
    logger.info(f"  Output topic: {settings.kafka_output_topic}")
    logger.info(f"  Consumer group: {settings.kafka_consumer_group}")
    logger.info(
        f"  Indicators: EMA-14, RSI-{settings.rsi_period}, "
        f"MACD({settings.ema_short_period},{settings.ema_long_period},{settings.macd_signal_period})"
    )

    # Initialize the Quixstreams Application
    app = Application(
        broker_address=settings.kafka_broker_address,
        consumer_group=settings.kafka_consumer_group,
        auto_offset_reset="earliest",
    )

    # Define input topic — OHLCV candles (JSON)
    input_topic = app.topic(
        settings.kafka_input_topic,
        value_deserializer="json",
    )

    # Define output topic — computed features (JSON)
    output_topic = app.topic(
        settings.kafka_output_topic,
        value_serializer="json",
    )

    # Create a StreamingDataFrame from the input topic
    sdf = app.dataframe(input_topic)

    # Apply the indicator computation
    sdf = sdf.apply(process_candle)

    # Filter out None results (not enough history yet)
    sdf = sdf.filter(lambda value: value is not None)

    # Log each emitted feature row
    sdf = sdf.update(lambda features: logger.info(f"Features: {features}"))

    # Produce to the output topic
    sdf = sdf.to_topic(output_topic)

    # Run the application
    logger.info("Running technical_indicators pipeline...")
    app.run()


if __name__ == "__main__":
    main()
