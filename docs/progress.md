# Progress Log

Use this file to track where you are. Update it at the **end of every session**, before you `git push`.

Format:

```
## YYYY-MM-DD — Session N: <title>
- ✅ Done: <what you finished>
- 🟡 In progress: <what's half-done>
- ⏭️ Next: <what to start with next session>
- 📝 Notes: <anything tricky to remember; commands, gotchas>
```

---

## 2026-05-08 — Pre-session: setup
- ✅ Done: 3-folder structure (master / reference / rebuild) created; GitHub repo `Bhujith10/Real-World-ML-Project-rebuild` created and initial push successful.
- ⏭️ Next: Session 0 (env setup) — install WSL2 + Ubuntu 24.04.
- 📝 Notes: Devcontainer approach abandoned — Windsurf's built-in Dev Containers extension can't parse valid JSON. Pivoting to WSL2 + manual install via mise.

## 2026-05-09 — Planning: hybrid path chosen
- ✅ Done: Reviewed scope. Decided on hybrid plan — minimum-viable crypto (6 sessions) then pivot to LLM-centric project (~9 phases). Wrote complete plan as `docs/*.md`.
- ⏭️ Next: Run `wsl --install -d Ubuntu-24.04` in admin PowerShell, then follow `docs/01-session-0-environment.md` step by step.
- 📝 Notes: All future sessions should follow the doc structure. Tear down kind cluster between sessions to save RAM.

## 2026-05-21 — Session 1: kind cluster + Kafka + trades service
- ✅ Done: kind cluster with port mappings, Kafka (official apache/kafka:3.9.0 in KRaft mode), Kafka UI (NodePort at localhost:8182), trades service (Kraken WebSocket → Kafka producer) running as K8s Deployment with live BTC/USD trades visible in Kafka UI.
- 📝 Notes: Bitnami images removed from Docker Hub (2025 deprecation) — switched to official apache/kafka image with plain K8s manifests instead of Helm. Used `docker save | ctr import` to load images into kind (workaround for containerd image store compatibility). Added `/etc/hosts` entry for `kafka-0.kafka-headless.kafka.svc.cluster.local` → 127.0.0.1 for local dev.
- ⏭️ Next: Session 2 — Containerize properly (multi-stage Dockerfile, K8s manifests, CI/CD, pre-commit, structured logging)

## 2026-05-28 — Session 2: Containerize + deploy + tooling
- ✅ Done: pre-commit + ruff (lint/format on every commit), uv workspaces (monorepo), structured JSON logging with loguru, .dockerignore, Makefile, build/deploy scripts, kustomize overlay, GitHub Actions CI pipeline.
- 📝 Notes: Used `dependency-groups.dev` instead of deprecated `tool.uv.dev-dependencies`. Multi-document YAML needs `--allow-multiple-documents` flag in check-yaml hook. `pre-commit run --all-files` passes cleanly.
- ⏭️ Next: Session 3 — Candles service (Kafka consumer → 1-min OHLCV windowing with Quixstreams)

## 2026-05-28 — Session 3: Candles service (OHLCV windowing)
- ✅ Done: candles service consuming from `trades` topic, windowing into 1-min OHLCV candles using Quixstreams (tumbling window + First/Last/Min/Max/Sum aggregators), producing to `candles` topic. Deployed to kind cluster and verified live candle output in logs.
- 📝 Notes: Quixstreams auto-creates topics (`candles`, changelog topic for state). Uses event-time windowing via custom timestamp_extractor. `.final()` emits only after window closes. `auto_offset_reset="earliest"` replays all historical trades on first start.
- ⏭️ Next: Session 4 — Technical indicators service (RSI/MACD/EMA from candles → RisingWave feature store)

## 2026-06-15 — Session 4: RisingWave feature store + technical indicators
- ✅ Done: RisingWave deployed to kind cluster (standalone single_node mode with custom TOML config for compactor memory tuning). Materialized views created: Kafka source table on `candles` topic, `mv_ema` (EMA-14), `mv_rsi` (RSI-14), `mv_macd` (MACD 12/26/9), `mv_features` (combined), and Kafka sink to `features` topic. Python `technical_indicators` service built and deployed — computes EMA/RSI/MACD via Quixstreams as an alternative to the SQL views. Both paths verified with live data flowing.
- 📝 Notes: RisingWave v2.3.0 hits compactor memory assertion (`compactor_memory_limit_bytes > min_compactor_memory_limit_bytes * 2`) with default config — fixed by mounting a custom `risingwave.toml` setting `compactor_memory_limit_mb = 1024` and `compactor_max_sst_size = 134217728`. Docker Desktop on WSL2 had extremely slow networking inside build containers — fixed by adding `"dns": ["8.8.8.8", "8.8.4.4"]` to Docker Engine config. Switched `technical_indicators` Dockerfile from `uv sync` to `pip install` due to `uv` download issues in Docker. All three service Dockerfiles updated with `UV_LINK_MODE=copy`, `UV_HTTP_TIMEOUT=120`, and `--mount=type=cache` for future builds.
- ⏭️ Next: Session 5 — Predictor service (XGBoost + MLflow train/inference)

---

<!-- Add new entries above this line -->
