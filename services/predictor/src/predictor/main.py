"""Entry point for the predictor service.

This service:
1. Loads the latest registered model from MLflow at startup
2. Consumes feature rows from the "features" Kafka topic
3. Makes a price prediction for each feature row using XGBoost
4. Produces predictions to the "predictions" Kafka topic

Run with: uv run python -m predictor
"""

import numpy as np
from loguru import logger
from quixstreams import Application

from predictor.config import settings
from predictor.logging import setup_logging
from predictor.schemas import FeatureRow, Prediction


def load_model():
    """Load the latest model version from MLflow registry.

    Returns the model object, or None if no model is registered yet.
    The model is loaded once at startup and kept in memory — predictions
    are just numpy calls, no network overhead per message.

    We first check if the model exists in the registry via the search API
    to avoid hanging on load_model() when no model is registered.
    """
    import mlflow
    from mlflow.exceptions import MlflowException

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)

    # First, check if the model is registered at all
    try:
        client = mlflow.MlflowClient()
        versions = client.search_model_versions(
            f"name='{settings.mlflow_model_name}'",
            max_results=1,
        )
        if not versions:
            logger.warning(
                f"No model '{settings.mlflow_model_name}' in registry. "
                "Running in pass-through mode."
            )
            return None
    except MlflowException as e:
        logger.warning(f"Could not query MLflow registry ({e}). Running in pass-through mode.")
        return None

    # Model exists — load it
    model_uri = f"models:/{settings.mlflow_model_name}/latest"
    try:
        model = mlflow.xgboost.load_model(model_uri)
        logger.info(f"Loaded model from {model_uri}")
        return model
    except Exception as e:
        logger.warning(f"Failed to load model ({e}). Running in pass-through mode.")
        return None


def make_prediction(model, row: dict) -> dict:
    """Given a feature row and a model, produce a prediction message.

    If no model is loaded, returns a dummy prediction with current_price
    as the predicted price (pass-through mode for testing).

    Validates input via FeatureRow and output via Prediction (Pydantic).
    """
    # Validate incoming message
    feature_row = FeatureRow(**row)
    current_price = feature_row.current_close

    if model is not None:
        # Build feature array in the exact order the model expects
        features = []
        for col in settings.feature_columns:
            val = getattr(feature_row, col)
            # Replace None/null with 0.0 — the model was trained with clean data,
            # but early candles may not have enough history for EMA/RSI/MACD
            features.append(float(val) if val is not None else 0.0)

        feature_array = np.array([features], dtype=np.float32)
        predicted_price = float(model.predict(feature_array)[0])
        model_version = "latest"
    else:
        # No model loaded — pass-through mode for testing the pipeline
        predicted_price = current_price
        model_version = "none"

    # Validate outgoing message
    prediction = Prediction(
        pair=feature_row.pair,
        window_start_ms=feature_row.window_start_ms,
        current_price=current_price,
        predicted_price_5min=round(predicted_price, 2),
        model_version=model_version,
    )
    return prediction.model_dump()


def main() -> None:
    """Set up logging, load model, and run the streaming prediction pipeline."""
    setup_logging()

    logger.info("Starting predictor service")
    logger.info(f"  Input topic:    {settings.kafka_input_topic}")
    logger.info(f"  Output topic:   {settings.kafka_output_topic}")
    logger.info(f"  MLflow URI:     {settings.mlflow_tracking_uri}")
    logger.info(f"  Model name:     {settings.mlflow_model_name}")
    logger.info(f"  Consumer group: {settings.kafka_consumer_group}")

    # Load model once at startup
    model = load_model()

    # Initialize the Quixstreams Application
    app = Application(
        broker_address=settings.kafka_broker_address,
        consumer_group=settings.kafka_consumer_group,
        auto_offset_reset="latest",
    )

    # Define input and output topics
    input_topic = app.topic(
        settings.kafka_input_topic,
        value_deserializer="json",
    )
    output_topic = app.topic(
        settings.kafka_output_topic,
        value_serializer="json",
    )

    # Build the streaming pipeline
    sdf = app.dataframe(input_topic)

    # Apply prediction to each incoming feature row
    sdf = sdf.apply(lambda row: make_prediction(model, row))

    # Log each prediction
    sdf = sdf.update(
        lambda pred: logger.info(
            f"Prediction: {pred['pair']} "
            f"current=${pred['current_price']:.2f} "
            f"predicted=${pred['predicted_price_5min']:.2f} "
            f"(model={pred['model_version']})"
        )
    )

    # Produce to the output topic
    sdf = sdf.to_topic(output_topic)

    # Run the application (blocks forever, processing the stream)
    logger.info("Running predictor pipeline...")
    app.run()


if __name__ == "__main__":
    main()
