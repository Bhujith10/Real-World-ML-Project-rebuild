"""Pydantic models for the predictor service.

Defines the shape of messages consumed (features) and produced (predictions).
"""

from pydantic import BaseModel


class FeatureRow(BaseModel):
    """A single feature row consumed from the features Kafka topic.

    Produced by RisingWave's sink_features (mv_features materialized view).
    """

    pair: str
    window_start_ms: int
    window_end_ms: int
    current_close: float
    ema_14: float | None = None
    rsi_14: float | None = None
    macd_line: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None


class Prediction(BaseModel):
    """A single prediction produced to the predictions Kafka topic."""

    pair: str
    window_start_ms: int
    current_price: float
    predicted_price_5min: float
    model_version: str
