"""Configuration for the predictor service.

All settings are loaded from environment variables (or use defaults for local dev).
Same pattern as the trades and candles services.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Kafka connection
    kafka_broker_address: str = "kafka-0.kafka-headless.kafka.svc.cluster.local:9092"

    # Input topic — features computed by RisingWave
    kafka_input_topic: str = "features"

    # Output topic — predictions
    kafka_output_topic: str = "predictions"

    # Consumer group ID
    kafka_consumer_group: str = "predictor-service"

    # MLflow tracking server URI
    mlflow_tracking_uri: str = "http://mlflow.mlflow.svc.cluster.local:5000"

    # MLflow model name in the registry
    mlflow_model_name: str = "crypto-price-predictor"

    # Feature columns expected by the model (must match training)
    feature_columns: list[str] = [
        "ema_14",
        "rsi_14",
        "macd_line",
        "macd_signal",
        "macd_histogram",
    ]

    # RisingWave connection (for training data queries)
    risingwave_host: str = "risingwave.risingwave.svc.cluster.local"
    risingwave_port: int = 4566
    risingwave_db: str = "dev"
    risingwave_user: str = "root"

    # Logging format: "text" for dev, "json" for production
    log_format: str = "text"

    class Config:
        env_prefix = ""


settings = Settings()
