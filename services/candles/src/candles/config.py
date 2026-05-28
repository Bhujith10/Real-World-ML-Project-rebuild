"""Configuration for the candles service.

All settings are loaded from environment variables (or use defaults for local dev).
Same pattern as the trades service — pydantic-settings handles the mapping.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Kafka connection
    kafka_broker_address: str = "kafka-0.kafka-headless.kafka.svc.cluster.local:9092"

    # Input topic — raw trades produced by the trades service
    kafka_input_topic: str = "trades"

    # Output topic — aggregated 1-min OHLCV candles
    kafka_output_topic: str = "candles"

    # Consumer group ID — Kafka tracks how far this group has read
    kafka_consumer_group: str = "candles-service"

    # Candle window duration in seconds
    candle_seconds: int = 60

    # Logging format: "text" for dev, "json" for production
    log_format: str = "text"

    class Config:
        env_prefix = ""


settings = Settings()
