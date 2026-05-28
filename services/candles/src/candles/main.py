"""Entry point for the candles service.

This service:
1. Consumes raw trade messages from the "trades" Kafka topic
2. Windows them into 1-minute buckets using Quixstreams
3. Aggregates each window into an OHLCV candle (open, high, low, close, volume)
4. Produces the completed candle to the "candles" Kafka topic

Run with: uv run python -m candles.main
"""

from datetime import timedelta

from loguru import logger
from quixstreams import Application
from quixstreams.dataframe.windows import First, Last, Max, Min, Sum
from quixstreams.models import TimestampType

from candles.config import settings
from candles.logging import setup_logging


def timestamp_extractor(
    value: dict,
    headers: list | None,
    timestamp: float,
    timestamp_type: TimestampType,
) -> int:
    """Extract event time from the trade message payload.

    Our trades have a "timestamp" field (ISO format string from Kraken).
    We convert it to milliseconds for Quixstreams windowing.
    This ensures windows are based on when the trade HAPPENED (event time),
    not when it was processed (processing time).
    """
    from datetime import datetime

    trade_time = datetime.fromisoformat(value["timestamp"])
    return int(trade_time.timestamp() * 1000)


def format_candle(value: dict) -> dict:
    """Transform the raw window aggregation output into a clean candle schema.

    Input from Quixstreams:
      {"start": <ms>, "end": <ms>, "open": ..., "high": ..., ...}

    Output (what we produce to the candles topic):
      {"pair": ..., "open": ..., "high": ..., "low": ..., "close": ...,
       "volume": ..., "window_start_ms": ..., "window_end_ms": ...}
    """
    return {
        "pair": value["pair"],
        "open": value["open"],
        "high": value["high"],
        "low": value["low"],
        "close": value["close"],
        "volume": round(value["volume"], 8),
        "window_start_ms": value["start"],
        "window_end_ms": value["end"],
    }


def main() -> None:
    """Set up logging, configure the Quixstreams app, and run the pipeline."""
    setup_logging()

    logger.info("Starting candles service")
    logger.info(f"  Input topic:  {settings.kafka_input_topic}")
    logger.info(f"  Output topic: {settings.kafka_output_topic}")
    logger.info(f"  Window size:  {settings.candle_seconds}s")
    logger.info(f"  Consumer group: {settings.kafka_consumer_group}")

    # Initialize the Quixstreams Application
    # This manages Kafka consumer + producer + state internally
    app = Application(
        broker_address=settings.kafka_broker_address,
        consumer_group=settings.kafka_consumer_group,
        auto_offset_reset="earliest",
    )

    # Define input topic — raw trades (JSON)
    input_topic = app.topic(
        settings.kafka_input_topic,
        value_deserializer="json",
        timestamp_extractor=timestamp_extractor,
    )

    # Define output topic — aggregated candles (JSON)
    output_topic = app.topic(
        settings.kafka_output_topic,
        value_serializer="json",
    )

    # Create a StreamingDataFrame from the input topic
    sdf = app.dataframe(input_topic)

    # Apply a tumbling window and aggregate into OHLCV
    sdf = (
        sdf.tumbling_window(timedelta(seconds=settings.candle_seconds))
        .agg(
            open=First("price"),
            high=Max("price"),
            low=Min("price"),
            close=Last("price"),
            volume=Sum("volume"),
            pair=Last("pair"),
        )
        .final()
    )

    # Transform the windowed result into our clean candle schema
    sdf = sdf.apply(format_candle)

    # Log each emitted candle
    sdf = sdf.update(lambda candle: logger.info(f"Candle: {candle}"))

    # Produce to the output topic
    sdf = sdf.to_topic(output_topic)

    # Run the application (blocks forever, processing the stream)
    logger.info("Running candles pipeline...")
    app.run()


if __name__ == "__main__":
    main()
