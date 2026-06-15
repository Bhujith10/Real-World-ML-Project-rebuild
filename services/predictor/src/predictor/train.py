"""Training script for the crypto price predictor.

This script:
1. Loads historical feature data from RisingWave (or a Parquet file)
2. Engineers the target: price 5 minutes ahead (shift close by 5 rows)
3. Splits data by time (no shuffle — critical for time series!)
4. Trains an XGBoost regressor
5. Logs metrics, parameters, and model to MLflow
6. Registers the model in MLflow's model registry

Run manually:  uv run python -m predictor.train
Run in cluster: kubectl exec / Job (future)

NOTE: You need enough accumulated data in RisingWave before training.
      The model quality depends on having at least a few hours of candles.
"""

import mlflow
import numpy as np
import polars as pl
import xgboost as xgb
from loguru import logger

from predictor.config import settings
from predictor.feature_loader import export_to_parquet, load_from_parquet, load_from_risingwave
from predictor.logging import setup_logging

# Number of candles ahead to predict (5 candles × 1 min = 5 minutes)
PREDICTION_HORIZON = 5

# Train/test split ratio (80% train, 20% test — by time, not random)
TRAIN_RATIO = 0.8


def engineer_target(df: pl.DataFrame) -> pl.DataFrame:
    """Create the prediction target: close price N candles ahead.

    For each row at time T, the target is the close price at T + PREDICTION_HORIZON.
    Rows at the end without a future price are dropped (they have null targets).
    """
    df = df.with_columns(
        pl.col("current_close").shift(-PREDICTION_HORIZON).alias("target_price"),
    )
    # Drop rows where target is null (last PREDICTION_HORIZON rows)
    df = df.drop_nulls(subset=["target_price"])
    return df


def train_model(
    source: str = "risingwave",
    parquet_path: str | None = None,
    export_path: str | None = None,
) -> None:
    """End-to-end training pipeline.

    Args:
        source: "risingwave" to query live data, "parquet" to read from file
        parquet_path: Path to Parquet file (required if source="parquet")
        export_path: If set, export the loaded features to this Parquet path
    """
    setup_logging()

    logger.info("=" * 60)
    logger.info("Starting model training")
    logger.info("=" * 60)

    # Step 1: Load features
    if source == "parquet" and parquet_path:
        df = load_from_parquet(parquet_path)
    else:
        df = load_from_risingwave()

    if export_path:
        export_to_parquet(df, export_path)

    logger.info(f"Raw features shape: {df.shape}")

    if len(df) < PREDICTION_HORIZON + 10:
        logger.error(
            f"Not enough data to train. Need at least {PREDICTION_HORIZON + 10} rows, "
            f"got {len(df)}. Let the system collect more candles and try again."
        )
        return

    # Step 2: Engineer target
    df = engineer_target(df)
    logger.info(f"After target engineering: {df.shape}")

    # Step 3: Prepare feature matrix and target vector
    feature_cols = settings.feature_columns
    logger.info(f"Feature columns: {feature_cols}")

    # Fill nulls with 0 (early candles may lack EMA/RSI/MACD history)
    X = df.select(feature_cols).fill_null(0.0).to_numpy().astype(np.float32)
    y = df["target_price"].to_numpy().astype(np.float32)

    # Step 4: Time-based train/test split (no shuffle!)
    split_idx = int(len(X) * TRAIN_RATIO)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    logger.info(f"Train set: {X_train.shape[0]} rows")
    logger.info(f"Test set:  {X_test.shape[0]} rows")

    # Step 5: Train XGBoost
    params = {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "objective": "reg:squarederror",
    }
    logger.info(f"XGBoost params: {params}")

    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train)

    # Step 6: Evaluate
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    mae_train = float(np.mean(np.abs(y_train - y_pred_train)))
    mae_test = float(np.mean(np.abs(y_test - y_pred_test)))
    rmse_train = float(np.sqrt(np.mean((y_train - y_pred_train) ** 2)))
    rmse_test = float(np.sqrt(np.mean((y_test - y_pred_test) ** 2)))

    logger.info(f"Train MAE:  ${mae_train:.2f}")
    logger.info(f"Test MAE:   ${mae_test:.2f}")
    logger.info(f"Train RMSE: ${rmse_train:.2f}")
    logger.info(f"Test RMSE:  ${rmse_test:.2f}")

    # Step 7: Log to MLflow
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment("crypto-price-prediction")

    with mlflow.start_run(run_name="xgboost-price-5min") as run:
        # Log parameters
        mlflow.log_params(params)
        mlflow.log_param("prediction_horizon", PREDICTION_HORIZON)
        mlflow.log_param("train_size", X_train.shape[0])
        mlflow.log_param("test_size", X_test.shape[0])
        mlflow.log_param("feature_columns", ",".join(feature_cols))

        # Log metrics
        mlflow.log_metric("mae_train", mae_train)
        mlflow.log_metric("mae_test", mae_test)
        mlflow.log_metric("rmse_train", rmse_train)
        mlflow.log_metric("rmse_test", rmse_test)

        # Log and register model
        mlflow.xgboost.log_model(
            model,
            artifact_path="model",
            registered_model_name=settings.mlflow_model_name,
        )

        logger.info(f"MLflow run ID: {run.info.run_id}")
        logger.info(f"Model registered as '{settings.mlflow_model_name}'")

    logger.info("=" * 60)
    logger.info("Training complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    train_model()
