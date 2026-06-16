# Crypto MVP — Real-Time Price Prediction System

A real-time ML system that predicts BTC/USD prices 5 minutes ahead, running on local Kubernetes.

## Architecture

```
Kraken WebSocket
      │
      ▼
┌──────────┐  topic: trades   ┌──────────┐  topic: candles   ┌────────────┐
│  trades  │─────────────────▶│ candles  │──────────────────▶│ RisingWave │
└──────────┘                  └──────────┘                   │ (streaming │
                                                             │    SQL)    │
                                                             └────────────┘
                                                                   │
                                                          topic: features
                                                                   │
                                                                   ▼
                                                            ┌────────────┐  topic: predictions
                                                            │ predictor  │─────────────────────▶ Grafana
                                                            │ (XGBoost)  │
                                                            └────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Orchestration | Kubernetes (kind) |
| Streaming | Apache Kafka (KRaft mode) |
| Stream processing | Quixstreams (Python) |
| Feature store | RisingWave (streaming SQL) |
| Model registry | MLflow |
| Model | XGBoost (gradient-boosted trees) |
| Dashboard | Grafana |
| Config | pydantic-settings |
| Logging | loguru (structured JSON) |

## Services

| Service | Description |
|---------|-------------|
| `services/trades/` | Connects to Kraken WebSocket, streams raw trades to Kafka |
| `services/candles/` | Aggregates trades into 1-minute OHLCV candles (tumbling window) |
| `services/predictor/` | Loads XGBoost model from MLflow, makes price predictions per feature row |

## Quick Start

**Prerequisites:** Docker, kind, kubectl, psql, uv

```bash
# Spin up everything from scratch (~10 min)
bash scripts/spin-up.sh

# Or step by step:
make cluster          # Create kind cluster
make kafka            # Deploy Kafka
make kafka-ui         # Deploy Kafka UI
make risingwave       # Deploy RisingWave
make risingwave-views # Apply materialized views
make mlflow           # Deploy MLflow
make grafana          # Deploy Grafana
make build-trades build-candles build-predictor  # Build images
make deploy-trades deploy-candles deploy-predictor  # Deploy services
```

## Accessing UIs

| UI | URL | Credentials |
|----|-----|-------------|
| Kafka UI | http://localhost:8182 | — |
| MLflow | http://localhost:5000 | — |
| Grafana | http://localhost:3000 | admin / admin |
| RisingWave | `psql -h localhost -p 4566 -d dev -U root` | — |

## Training the Model

```bash
cd services/predictor
uv run python -m predictor train
```

This pulls features from RisingWave, trains XGBoost, and registers the model in MLflow if it improves on the previous version.

## Teardown

```bash
bash scripts/teardown.sh
```

Deletes the kind cluster. Local parquet data (`services/predictor/data/`) is preserved.

## Project Structure

```
├── deployments/dev/       # Kubernetes manifests
│   ├── kind/              # Cluster config
│   ├── kafka/             # Kafka + Kafka UI
│   ├── risingwave/        # RisingWave + materialized views
│   ├── mlflow/            # MLflow server
│   ├── grafana/           # Grafana + dashboards
│   ├── trades/            # trades deployment
│   ├── candles/           # candles deployment
│   └── predictor/         # predictor deployment
├── docker/                # Dockerfiles
├── scripts/               # Build, deploy, spin-up, teardown
├── services/              # Application code
│   ├── trades/
│   ├── candles/
│   └── predictor/
└── Makefile               # Convenience targets
```
