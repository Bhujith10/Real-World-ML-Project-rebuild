"""Training script for the crypto price predictor.

Full pipeline:
1. Pull data from RisingWave → save as timestamped Parquet in data/raw/
2. Build canonical dataset: concat all raw Parquets → dedup → sort
3. Check if enough new rows since last training (skip if not)
4. Detect gaps in the data (timestamp jumps > threshold)
5. Engineer targets (price 5 min ahead), respecting gap boundaries
6. Time-based 80/20 split (no shuffle — critical for time series)
7. Train XGBoost regressor
8. Compare with previous model on the SAME test set
9. Only register the new model if it beats the previous one (lower MAE)
10. Log everything to MLflow
11. If a new model was registered, restart the predictor deployment

Run locally:
  RISINGWAVE_HOST=localhost MLFLOW_TRACKING_URI=http://localhost:5000 \
    uv run python -m predictor.train

Requires RisingWave at port 4566 and MLflow at port 5000 (both via NodePort).
"""

import json
import subprocess
from datetime import UTC
from pathlib import Path

import mlflow
import numpy as np
import polars as pl
import xgboost as xgb
from loguru import logger
from mlflow.exceptions import MlflowException

from predictor.config import settings
from predictor.feature_loader import (
    build_canonical_dataset,
    detect_gaps,
    export_raw_parquet,
    pull_from_risingwave,
)
from predictor.logging import setup_logging

# Number of candles ahead to predict (5 candles × 1 min = 5 minutes)
PREDICTION_HORIZON = 5

# Train/test split ratio (80% train, 20% test — by time, not random)
TRAIN_RATIO = 0.8

# Minimum rows required to attempt training
MIN_ROWS = 50

# Minimum NEW rows required since last training run to justify retraining
MIN_NEW_ROWS = 100

# Path to the metadata file tracking last training run
TRAIN_INFO_FILE = Path(settings.data_dir) / "last_train_info.json"


def engineer_targets(df: pl.DataFrame) -> pl.DataFrame:
    """Create prediction targets respecting gap boundaries.

    For each row at time T within a contiguous block, the target is the
    close price at T + PREDICTION_HORIZON. Targets are NOT created across
    gap boundaries — we shift within each gap_group independently.

    Requires 'gap_group' column from detect_gaps().
    """
    result_dfs = []
    for group_id in sorted(df["gap_group"].unique().to_list()):
        block = df.filter(pl.col("gap_group") == group_id)

        block = block.with_columns(
            pl.col("current_close").shift(-PREDICTION_HORIZON).alias("target_price"),
        )
        # Drop rows without a target (last PREDICTION_HORIZON rows per block)
        block = block.drop_nulls(subset=["target_price"])
        result_dfs.append(block)

    if not result_dfs:
        return pl.DataFrame()

    result = pl.concat(result_dfs)
    logger.info(
        f"After target engineering: {len(result)} rows "
        f"(dropped {len(df) - len(result)} rows at block boundaries)"
    )
    return result


def evaluate_model(
    model: xgb.XGBRegressor,
    X: np.ndarray,
    y: np.ndarray,
    label: str,
) -> dict[str, float]:
    """Compute MAE and RMSE for a model on a dataset."""
    y_pred = model.predict(X)
    mae = float(np.mean(np.abs(y - y_pred)))
    rmse = float(np.sqrt(np.mean((y - y_pred) ** 2)))
    logger.info(f"{label} MAE:  ${mae:.2f}")
    logger.info(f"{label} RMSE: ${rmse:.2f}")
    return {"mae": mae, "rmse": rmse}


def load_train_info() -> dict | None:
    """Load metadata from the last training run.

    Returns dict with keys: row_count, timestamp, model_version
    or None if no previous training info exists.
    """
    if not TRAIN_INFO_FILE.exists():
        return None
    try:
        return json.loads(TRAIN_INFO_FILE.read_text())
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not read {TRAIN_INFO_FILE}: {e}")
        return None


def save_train_info(row_count: int, registered: bool) -> None:
    """Save metadata about this training run."""
    from datetime import datetime

    info = {
        "row_count": row_count,
        "timestamp": datetime.now(UTC).isoformat(),
        "model_registered": registered,
    }
    TRAIN_INFO_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRAIN_INFO_FILE.write_text(json.dumps(info, indent=2))
    logger.info(f"Saved training info to {TRAIN_INFO_FILE}")


def restart_predictor() -> None:
    """Restart the predictor deployment so it loads the new model.

    Uses kubectl to do a rolling restart. Only works when running
    inside the cluster (CronJob) with the predictor-trainer ServiceAccount.
    When running locally, this is a no-op.
    """
    try:
        result = subprocess.run(
            [
                "kubectl",
                "rollout",
                "restart",
                "deployment/predictor",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info("Predictor deployment restarted to load new model")
        else:
            logger.warning(
                f"Could not restart predictor (rc={result.returncode}): " f"{result.stderr.strip()}"
            )
    except FileNotFoundError:
        logger.info("kubectl not available — running locally, skip predictor restart")
    except subprocess.TimeoutExpired:
        logger.warning("kubectl rollout restart timed out")


def load_previous_model() -> xgb.XGBRegressor | None:
    """Load the latest registered model from MLflow, if any.

    Returns None if no model is registered.
    """
    try:
        client = mlflow.MlflowClient()
        versions = client.search_model_versions(
            f"name='{settings.mlflow_model_name}'",
            max_results=1,
        )
        if not versions:
            logger.info("No previous model in registry — this is the first training run")
            return None

        model_uri = f"models:/{settings.mlflow_model_name}/latest"
        prev_model = mlflow.xgboost.load_model(model_uri)
        logger.info(f"Loaded previous model from {model_uri}")
        return prev_model
    except MlflowException as e:
        logger.warning(f"Could not load previous model: {e}")
        return None


def train() -> None:
    """End-to-end training pipeline."""
    setup_logging()

    logger.info("=" * 60)
    logger.info("Starting model training pipeline")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # Step 1: Pull latest data from RisingWave → save to raw/
    # ------------------------------------------------------------------
    logger.info("Step 1: Pull data from RisingWave")
    fresh_df = pull_from_risingwave()

    if len(fresh_df) == 0:
        logger.error("No data in RisingWave. Cannot train.")
        return

    raw_path = export_raw_parquet(fresh_df)
    logger.info(f"Raw export saved to {raw_path}")

    # ------------------------------------------------------------------
    # Step 2: Build canonical dataset from all raw files
    # ------------------------------------------------------------------
    logger.info("Step 2: Build canonical dataset")
    df = build_canonical_dataset()

    if len(df) < MIN_ROWS:
        logger.error(
            f"Not enough data to train. Need at least {MIN_ROWS} rows, "
            f"got {len(df)}. Let the system collect more candles."
        )
        return

    logger.info(f"Canonical dataset shape: {df.shape}")

    # ------------------------------------------------------------------
    # Step 3: Check if enough new rows since last training
    # ------------------------------------------------------------------
    logger.info("Step 3: Check for new data")
    prev_info = load_train_info()
    if prev_info is not None:
        prev_rows = prev_info.get("row_count", 0)
        new_rows = len(df) - prev_rows
        logger.info(
            f"Previous training used {prev_rows} rows. "
            f"Current dataset has {len(df)} rows ({new_rows} new)."
        )
        if new_rows < MIN_NEW_ROWS:
            logger.info(f"Only {new_rows} new rows (need {MIN_NEW_ROWS}). " "Skipping training.")
            return
    else:
        logger.info("No previous training info found — first run.")

    # ------------------------------------------------------------------
    # Step 4: Detect gaps
    # ------------------------------------------------------------------
    logger.info("Step 4: Detect gaps")
    df = detect_gaps(df)

    # ------------------------------------------------------------------
    # Step 5: Engineer targets (respecting gaps)
    # ------------------------------------------------------------------
    logger.info("Step 5: Engineer targets")
    df = engineer_targets(df)

    if len(df) == 0:
        logger.error("No usable rows after target engineering. Need more data.")
        return

    # ------------------------------------------------------------------
    # Step 6: Prepare features and time-based split
    # ------------------------------------------------------------------
    logger.info("Step 6: Prepare features and split")
    feature_cols = settings.feature_columns

    # Fill nulls with 0 (early candles may lack EMA/RSI/MACD history)
    X = df.select(feature_cols).fill_null(0.0).to_numpy().astype(np.float32)
    y = df["target_price"].to_numpy().astype(np.float32)

    split_idx = int(len(X) * TRAIN_RATIO)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    logger.info(f"Train set: {X_train.shape[0]} rows")
    logger.info(f"Test set:  {X_test.shape[0]} rows")

    if X_test.shape[0] == 0:
        logger.error("Test set is empty. Need more data.")
        return

    # ------------------------------------------------------------------
    # Step 7: Train new XGBoost model
    # ------------------------------------------------------------------
    logger.info("Step 7: Train XGBoost")
    params = {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "objective": "reg:squarederror",
    }
    logger.info(f"XGBoost params: {params}")

    new_model = xgb.XGBRegressor(**params)
    new_model.fit(X_train, y_train)

    # Evaluate new model
    train_metrics = evaluate_model(new_model, X_train, y_train, "New model (train)")
    test_metrics = evaluate_model(new_model, X_test, y_test, "New model (test)")

    # ------------------------------------------------------------------
    # Step 8: Compare with previous model (on the SAME test set)
    # ------------------------------------------------------------------
    logger.info("Step 8: Compare with previous model")
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)

    prev_model = load_previous_model()

    should_register = True
    prev_test_metrics = None

    if prev_model is not None:
        prev_test_metrics = evaluate_model(prev_model, X_test, y_test, "Previous model (test)")
        if test_metrics["mae"] >= prev_test_metrics["mae"]:
            logger.warning(
                f"New model MAE (${test_metrics['mae']:.2f}) is NOT better than "
                f"previous (${prev_test_metrics['mae']:.2f}). "
                "Skipping model registration."
            )
            should_register = False
        else:
            improvement = prev_test_metrics["mae"] - test_metrics["mae"]
            logger.info(
                f"New model is better! MAE improved by ${improvement:.2f} "
                f"(${prev_test_metrics['mae']:.2f} → ${test_metrics['mae']:.2f})"
            )

    # ------------------------------------------------------------------
    # Step 9: Log to MLflow (always log run, conditionally register model)
    # ------------------------------------------------------------------
    logger.info("Step 9: Log to MLflow")
    mlflow.set_experiment("crypto-price-predictor")

    with mlflow.start_run(run_name="xgboost-price-5min") as run:
        # Log parameters
        mlflow.log_params(params)
        mlflow.log_param("prediction_horizon", PREDICTION_HORIZON)
        mlflow.log_param("train_size", X_train.shape[0])
        mlflow.log_param("test_size", X_test.shape[0])
        mlflow.log_param("total_rows", len(df))
        mlflow.log_param("feature_columns", ",".join(feature_cols))
        mlflow.log_param("data_dir", str(settings.data_dir))
        mlflow.log_param("gap_threshold_minutes", settings.gap_threshold_minutes)

        # Log new model metrics
        mlflow.log_metric("mae_train", train_metrics["mae"])
        mlflow.log_metric("mae_test", test_metrics["mae"])
        mlflow.log_metric("rmse_train", train_metrics["rmse"])
        mlflow.log_metric("rmse_test", test_metrics["rmse"])

        # Log previous model metrics for comparison
        if prev_test_metrics is not None:
            mlflow.log_metric("prev_mae_test", prev_test_metrics["mae"])
            mlflow.log_metric("prev_rmse_test", prev_test_metrics["rmse"])

        mlflow.log_metric("model_registered", 1.0 if should_register else 0.0)

        # Register model only if it beats the previous one
        registered_name = settings.mlflow_model_name if should_register else None
        mlflow.xgboost.log_model(
            new_model,
            artifact_path="model",
            registered_model_name=registered_name,
        )

        logger.info(f"MLflow run ID: {run.info.run_id}")
        if should_register:
            logger.info(f"Model registered as '{settings.mlflow_model_name}'")
        else:
            logger.info("Model logged but NOT registered (did not beat previous)")

    # ------------------------------------------------------------------
    # Step 10: Save training metadata
    # ------------------------------------------------------------------
    save_train_info(row_count=len(df), registered=should_register)

    # ------------------------------------------------------------------
    # Step 11: Restart predictor if a new model was registered
    # ------------------------------------------------------------------
    if should_register:
        logger.info("Step 11: Restarting predictor to load new model")
        restart_predictor()

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Training pipeline complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    train()
