# Crypto MVP — Real-Time Price Prediction System

**Total effort:** ~30 hours across 6 sessions
**End state:** 5 microservices on local Kubernetes, processing live Kraken trades, predicting prices 5 min ahead, with Grafana dashboard + GitHub Actions CI/CD.

## Why we're building this

To gain hands-on experience with the production stack: **Kafka, Kubernetes, Docker, MLflow, streaming SQL, CI/CD, observability.** The crypto domain is just a vehicle — these skills transfer to any data/ML role.

## Architecture

```
Kraken WebSocket
        │
        ▼
   ┌──────────┐   topic: trades        ┌──────────┐   topic: candles      ┌─────────────────┐
   │  trades  │───────────────────────▶│ candles  │──────────────────────▶│ tech_indicators │
   └──────────┘                        └──────────┘                       └─────────────────┘
                                                                                  │
                                                                                  ▼
                                                                          ┌──────────────┐
                                                                          │  RisingWave  │  ← feature store
                                                                          │ (streaming   │     (continuous SQL
                                                                          │     SQL)     │      materialized views)
                                                                          └──────────────┘
                                                                                  │
                                                          ┌───────────────────────┴────────────────────┐
                                                          ▼                                            ▼
                                                  ┌──────────────┐                            ┌──────────────┐
                                                  │  predictor   │   topic: predictions       │   Grafana    │
                                                  │  (XGBoost +  │───────────────────────────▶│  dashboard   │
                                                  │    MLflow)   │                            └──────────────┘
                                                  └──────────────┘
```

## Tech stack

| Component | Technology |
|---|---|
| Container runtime | Docker |
| Orchestration | Kubernetes (via `kind`) |
| Streaming bus | Apache Kafka (deployed via Strimzi/Helm) |
| Stream processing | Quixstreams (Python) |
| Feature store | RisingWave (Postgres-wire-compatible streaming DB) |
| Model registry | MLflow |
| Model | XGBoost (gradient-boosted trees) |
| Dashboards | Grafana |
| CI/CD | GitHub Actions |
| Image registry | GitHub Container Registry (GHCR) |
| Code quality | ruff, pre-commit |
| Config | pydantic-settings |
| Logging | loguru with structured JSON output |

## Sessions

### Session 1 — Kafka in cluster + first service (5–6 hrs)

**Build**
- Create local kind cluster with port mappings (`deployments/dev/kind/`)
- Deploy Kafka + Kafka UI via Helm (`deployments/dev/kafka/`)
- Write `services/trades/`: WebSocket client → Kafka producer
- Run locally with `uv run`, watch trades land in Kafka UI

**Files you create**
```
deployments/dev/kind/{create_cluster.sh,kind-with-portmapping.yaml}
deployments/dev/kafka/{install_kafka.sh,install_kafka_ui.sh}
services/trades/
├── pyproject.toml
├── README.md
└── src/trades/
    ├── __init__.py
    ├── main.py            # entry point
    ├── kraken_api.py      # WebSocket client
    ├── kafka_producer.py  # Kafka write
    └── schemas.py         # Pydantic models
```

**Concepts learned:** Kubernetes pods/services/deployments, Helm chart basics, port-forwarding, Kafka producers, async WebSocket clients.

**Definition of done**
- `kubectl get pods -n kafka` shows healthy Kafka + Kafka UI pods
- Open `http://localhost:8182` (Kafka UI), see live BTC trades streaming into the `trades` topic

---

### Session 2 — Containerize + deploy + tooling (5–6 hrs)

**Build**
- Multi-stage `Dockerfile` for trades service (target image size <300 MB)
- `.dockerignore`, `pyproject.toml` per service in monorepo (uv workspaces)
- K8s `Deployment` + `ConfigMap` + `Secret` YAML for trades
- `scripts/build-and-push-image.sh` + `scripts/deploy.sh`
- `Makefile` aliases: `make build-and-push`, `make deploy`
- GitHub Actions: build + push Docker images on push to main
- `pydantic-settings` for config (replaces hardcoded values)
- `pre-commit` + `ruff` configured, runs on every commit
- Structured JSON logging with `loguru`

**Files you create**
```
docker/trades.Dockerfile
.github/workflows/build-images.yml
deployments/dev/trades/{deployment.yaml,secret.yaml,kustomization.yaml}
scripts/{build-and-push-image.sh,deploy.sh}
Makefile
.pre-commit-config.yaml
```

**Concepts learned:** Multi-stage Docker builds, image size optimization, K8s secrets, kustomize basics, monorepo with uv workspaces, structured logging, CI basics.

**Definition of done**
- `docker images` shows your trades image at <300 MB
- `kubectl get pods` shows trades running, pulling image from GHCR
- Pushing to main triggers GH Actions, image appears in GHCR
- `pre-commit run --all-files` passes

---

### Session 3 — Stream processing with Quixstreams (5–6 hrs)

**Build**
- `services/candles/`: Kafka consumer (trades) → 1-minute OHLCV windowing → Kafka producer (candles)
- Use Quixstreams `tumbling_window` and `reduce` aggregations
- Tests: unit tests for the windowing logic with synthetic trades
- Deploy alongside trades; both running in cluster

**Files you create**
```
services/candles/
├── pyproject.toml
├── README.md
├── src/candles/
│   ├── main.py
│   ├── streaming_app.py
│   └── schemas.py
└── tests/
    └── test_windowing.py
```

**Concepts learned:** Stream processing patterns, time windows (tumbling vs hopping vs sliding), watermarks, late-arriving data, Quixstreams API, testing streaming code.

**Definition of done**
- Two services running in cluster
- `candles` topic in Kafka UI shows OHLCV records every minute
- `pytest services/candles/tests/` passes

---

### Session 4 — Feature store with RisingWave (5–6 hrs)

**Build**
- Deploy RisingWave to cluster (via official Helm chart)
- Define materialized views computing technical indicators (RSI, MACD, EMA) from `candles` topic
- `services/technical_indicators/`: thin Python service for any feature Quixstreams handles better than SQL
- Connect to RisingWave with `psql` from terminal, query feature rows

**Files you create**
```
deployments/dev/risingwave/{install.sh,materialized_views.sql}
services/technical_indicators/  (similar layout to candles)
```

**Concepts learned:** Streaming SQL, materialized views, feature stores, online vs offline features, online-offline feature skew prevention, Postgres wire protocol.

**Definition of done**
- `psql -h localhost -p 4566 -d dev` connects to RisingWave
- `SELECT * FROM mv_features LIMIT 5` returns continuously updated rows
- Indicators visible in Kafka UI on a `features` topic (if dual-publishing)

---

### Session 5 — Predictor service with MLflow (5–6 hrs)

**Build**
- Deploy MLflow to cluster (with Postgres backend + MinIO artifact store, or simpler local FS for now)
- `services/predictor/`:
  - **Training script** (`train.py`): reads historical features from RisingWave, trains XGBoost to predict `price_t+5min`, logs run, registers model
  - **Inference script** (`predict.py`): loads latest registered model, consumes live features, writes predictions to `predictions` topic
- Tests: model loading, feature schema validation
- Deploy predictor as inference pod in cluster

**Files you create**
```
deployments/dev/mlflow/install.sh
services/predictor/
├── pyproject.toml
├── README.md
├── src/predictor/
│   ├── train.py
│   ├── predict.py
│   ├── feature_loader.py
│   └── schemas.py
└── tests/
```

**Concepts learned:** MLflow tracking + registry, model versioning, train/serve parity, batch + online inference, XGBoost basics, time-series target engineering.

**Definition of done**
- MLflow UI at `http://localhost:5000` shows your training runs and registered model
- `predictor` pod is running, writing to `predictions` topic continuously
- Predictions visible in Kafka UI

---

### Session 6 — Dashboard + CI/CD polish (3–4 hrs)

**Build**
- Deploy Grafana to cluster
- Dashboard: live candles (line chart) + predictions overlaid; latency metrics from each service
- GitHub Actions improvements: run tests on PRs, deploy on tag releases
- Root README + per-service README (each: what, how to run, how to test)
- Tear-down + spin-up scripts so anyone can clone-and-run
- Final commit with version tag `v0.1.0-crypto-mvp`

**Files you create**
```
deployments/dev/grafana/{install.sh,dashboards/crypto.json}
.github/workflows/test.yml
README.md  (root)
services/*/README.md
scripts/{teardown.sh,spin-up.sh}
```

**Concepts learned:** Observability with Grafana, CI/CD discipline, documentation as code, project polish.

**Definition of done**
- `http://localhost:3000` shows Grafana dashboard with live candles + predictions
- A stranger could `git clone && ./scripts/spin-up.sh` and have everything running
- Repo tagged `v0.1.0-crypto-mvp`

---

## After the MVP

You will have:
- A working real-time ML system on K8s
- Comfortable with Docker + K8s + Kafka + MLflow + CI/CD
- A solid resume bullet
- Reusable infrastructure patterns (kind cluster, Helm installs, GH Actions) you'll directly reuse in the LLM project

Then we pivot to [03-llm-project.md](./03-llm-project.md).
