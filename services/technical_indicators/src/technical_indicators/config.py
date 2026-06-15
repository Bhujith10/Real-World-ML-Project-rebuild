"""Configuration for the technical_indicators service.

Uses pydantic-settings to read from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Kafka connection
    kafka_broker_address: str = "kafka-0.kafka-headless.kafka.svc.cluster.local:9092"

    # Input topic — OHLCV candles from the candles service
    kafka_input_topic: str = "candles"

    # Output topic — computed technical indicators (features)
    kafka_output_topic: str = "features"

    # Consumer group ID
    kafka_consumer_group: str = "technical-indicators-service"

    # EMA periods
    ema_short_period: int = 12
    ema_long_period: int = 26

    # RSI period
    rsi_period: int = 14

    # MACD signal period
    macd_signal_period: int = 9

    # Logging format: "text" for dev, "json" for production
    log_format: str = "text"

    class Config:
        env_prefix = ""


settings = Settings()
