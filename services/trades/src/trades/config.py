"""Configuration via environment variables using pydantic-settings.

pydantic-settings reads values from environment variables automatically.
For example, if you set KAFKA_BROKER_ADDRESS=kafka:9092 in your shell,
it will be picked up here without any code changes.

This keeps secrets and environment-specific values OUT of source code.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        kafka_broker_address: Kafka bootstrap server (host:port)
        kafka_topic: Topic name to produce trade messages to
        kraken_ws_url: Kraken WebSocket v2 API endpoint
        pairs: Comma-separated list of trading pairs to subscribe to
    """

    kafka_broker_address: str = "kafka-0.kafka-headless.kafka.svc.cluster.local:9092"
    kafka_topic: str = "trades"
    kraken_ws_url: str = "wss://ws.kraken.com/v2"
    pairs: str = "BTC/USD"
    log_format: str = "text"  # "text" for dev, "json" for production

    class Config:
        env_prefix = ""  # No prefix — use var names directly


settings = Settings()
