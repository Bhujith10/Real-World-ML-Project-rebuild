# predictor service

**What:** Loads the latest XGBoost model from MLflow and makes real-time price predictions (5 minutes ahead) for each incoming feature row.

**Architecture:**
```
Kafka topic: "features"
        |
        v
   +------------+
   | predictor  |  <- this service
   +------------+
        |
        v
Kafka topic: "predictions"
```

## How to run (inference)

```bash
cd services/predictor

# Install dependencies
uv sync

# Set environment variables (or use defaults for in-cluster)
export KAFKA_BROKER_ADDRESS="localhost:9092"
export KAFKA_INPUT_TOPIC="features"
export KAFKA_OUTPUT_TOPIC="predictions"
export MLFLOW_TRACKING_URI="http://localhost:5000"

# Run
uv run python -m predictor
```

## How to train

```bash
cd services/predictor

# Requires RisingWave to be accessible at localhost:4566
export RISINGWAVE_HOST="localhost"
export MLFLOW_TRACKING_URI="http://localhost:5000"

uv run python -m predictor train
```

Training will:
1. Pull all features from RisingWave
2. Export a timestamped parquet file to `data/raw/`
3. Build a canonical dataset (concat, deduplicate, sort)
4. Detect gaps in the time series
5. Engineer targets (price 5 minutes ahead)
6. Train XGBoost with time-based train/test split
7. Compare new model to the previously registered model
8. Register in MLflow only if test MAE improves

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `KAFKA_BROKER_ADDRESS` | `kafka-0.kafka-headless.kafka.svc.cluster.local:9092` | Kafka bootstrap server |
| `KAFKA_INPUT_TOPIC` | `features` | Topic to consume features from |
| `KAFKA_OUTPUT_TOPIC` | `predictions` | Topic to produce predictions to |
| `KAFKA_CONSUMER_GROUP` | `predictor-service` | Consumer group ID |
| `MLFLOW_TRACKING_URI` | `http://mlflow.mlflow.svc.cluster.local:5000` | MLflow server URI |
| `MLFLOW_MODEL_NAME` | `crypto-price-predictor` | Model name in MLflow registry |
| `RISINGWAVE_HOST` | `risingwave.risingwave.svc.cluster.local` | RisingWave host (for training) |
| `RISINGWAVE_PORT` | `4566` | RisingWave port |

## Message format (output JSON in Kafka)

```json
{
  "pair": "BTC/USD",
  "window_start_ms": 1700000000000,
  "current_price": 67234.5,
  "predicted_price_5min": 67290.2,
  "model_version": "latest"
}
```

## Data management

Historical feature data is stored in `data/raw/` as timestamped parquet files. These persist across cluster teardowns and are used to build the training dataset. The `.gitignore` ensures parquet files are not committed.
