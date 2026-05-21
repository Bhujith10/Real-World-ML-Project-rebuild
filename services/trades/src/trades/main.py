"""Entry point for the trades service.

This is the main loop:
1. Create a Kafka producer
2. Connect to Kraken WebSocket
3. For each trade received, produce it to Kafka
4. Log what's happening so we can see it working

Run with: uv run python -m trades.main
"""

import asyncio

from loguru import logger

from trades.config import settings
from trades.kafka_producer import create_producer, produce_trade
from trades.kraken_api import stream_trades


async def run() -> None:
    """Main async loop: stream trades from Kraken and produce to Kafka."""
    logger.info(f"Starting trades service")
    logger.info(f"  Kafka broker: {settings.kafka_broker_address}")
    logger.info(f"  Kafka topic:  {settings.kafka_topic}")
    logger.info(f"  Pairs:        {settings.pairs}")

    producer = create_producer()
    trade_count = 0

    try:
        async for trade in stream_trades():
            produce_trade(producer, trade)
            trade_count += 1

            # Log every 10th trade to avoid flooding the terminal
            if trade_count % 10 == 0:
                logger.info(
                    f"[{trade_count}] {trade.pair} | {trade.side} | "
                    f"price={trade.price} | vol={trade.volume}"
                )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        producer.flush()
        producer.close()
        logger.info(f"Producer closed. Total trades sent: {trade_count}")


def main() -> None:
    """Sync entry point that runs the async loop."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
