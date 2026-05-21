# Project Context — AI Agent Briefing

> **IMPORTANT:** This is a **learning activity**. The primary goal is not just to build a working system, but to understand every concept, tool, and decision deeply. Explain things from first principles when introducing new concepts. Do not skip steps or automate things the user should learn manually.

---

## Who I am

- Name: Bhujith (GitHub: Bhujith10)
- OS: Windows 11
- IDE: Windsurf (by Codeium) — with Cascade AI assistant
- Dev environment: WSL2 (Ubuntu) inside Windows, connected to Windsurf via WSL remote

---

## What I am building

A two-project learning journey covering the full stack of modern AI/ML engineering.

### Project 1 — Crypto MVP (Real-Time Price Prediction System)
A minimum-viable real-time crypto price prediction system running on local Kubernetes.

**Why:** To gain hands-on experience with Docker, Kubernetes, Kafka, stream processing, feature stores, MLflow, CI/CD, and observability — the production infrastructure skills every ML/data engineer needs.

**End state demo:**
- 5 microservices running in a local Kubernetes cluster (`kind`)
- Live BTC/ETH trade data from Kraken WebSocket → Kafka → stream processed → feature store → XGBoost model → predictions
- Grafana dashboard showing live candles + predictions overlaid
- GitHub Actions CI/CD pipeline
- Clean GitHub repo a stranger could clone and run

**Services to build:**
1. `trades` — WebSocket client → Kafka producer (live Kraken data)
2. `candles` — Kafka consumer → 1-min OHLCV windowing → Kafka producer (Quixstreams)
3. `technical_indicators` — RSI, MACD, EMA computation → RisingWave feature store
4. `predictor` — reads features, trains XGBoost, registers in MLflow, runs inference
5. `infra` — kind cluster, Kafka, Kafka UI, RisingWave, MLflow, Grafana (K8s YAML + Helm)

**Tech stack:** Docker, Kubernetes (kind), Apache Kafka (Strimzi/Helm), Quixstreams, RisingWave, MLflow, XGBoost, Grafana, GitHub Actions, GHCR, ruff, pre-commit, pydantic-settings, loguru, uv (monorepo), kustomize

---

### Project 2 — AI Research Workspace (LLM-Centric System)
A multi-agent research assistant that does RAG, GraphRAG, uses a fine-tuned LLM, and runs behind an API gateway.

**Why:** To learn the full LLM/AI engineering stack — agents, RAG, GraphRAG, fine-tuning, LLM serving, API gateway, rate limiting — the core skills of an AI Engineer at a modern LLM-centric company.

**What it does:** User gives a research topic → system searches arXiv/HN/blogs → retrieves and ranks documents (hybrid RAG) → builds a knowledge graph (GraphRAG) → multiple agents (researcher, critic, synthesizer) collaborate to produce a structured brief → user can chat with the brief.

**Tech stack:** FastAPI, LangGraph, Qdrant, BGE embeddings, Cohere re-ranker, Ragas, Neo4j, Hugging Face TRL+PEFT (LoRA), vLLM, Kong API gateway, Langfuse, Prometheus, Grafana, Loki, Instructor, Streamlit

---

## Current status

| Phase | Status |
|---|---|
| 3-folder structure + GitHub repo setup | ✅ Done |
| docs/ plan files written and pushed | ✅ Done |
| Session 0: WSL2 + all tools installed + Windsurf WSL connected | ✅ Done |
| **Session 1: kind cluster + Kafka + trades service** | **⏭️ NEXT** |

---

## Dev environment (fully set up)

- **WSL distro:** `Ubuntu` (set as default with `wsl --set-default Ubuntu`)
- **Project location in WSL:** `~/projects/Real-World-ML-Project-rebuild`
- **Windows copy** (do not use for development): `C:\Users\HP\Downloads\Real-World-ML-Project-rebuild`
- **GitHub repo:** https://github.com/Bhujith10/Real-World-ML-Project-rebuild
- **Docker Desktop:** running with WSL2 backend + Ubuntu integration enabled

**All tools verified inside WSL:**

| Tool | Version | How installed |
|---|---|---|
| Docker | 29.4.2 | Docker Desktop WSL integration |
| uv | latest | `curl astral.sh/uv` |
| mise | 2026.5.4 | `curl mise.run` |
| kubectl | 1.32.3 | mise |
| helm | 3.17.2 | mise |
| k9s | 0.40.10 | mise |
| kind | 0.24.0 | direct binary |
| jq | 1.7.1 | mise |
| yq | 4.45.1 | mise |
| kustomize | 5.6.0 | mise |
| pre-commit | 4.6.0 | uv tool install |
| direnv | 2.32.1 | apt |
| psql | 16.13 | apt |

**Important notes:**
- `kind`, `kubectl`, `helm`, and all tools are installed INSIDE WSL Ubuntu — NOT on Windows
- Always run project commands from the WSL terminal (bash), never from Windows PowerShell
- The Windsurf terminal defaults to PowerShell when in Windows mode — must connect to WSL first

---

## Repo structure (current)

```
Real-World-ML-Project-rebuild/
├── .editorconfig
├── .envrc
├── .gitignore
├── README.md
├── mise.toml                        ← pins tool versions
└── docs/
    ├── README.md                    ← index of all docs
    ├── 00-roadmap.md                ← big picture, timeline, working principles
    ├── 01-session-0-environment.md  ← WSL2 setup reference
    ├── 02-crypto-mvp.md             ← detailed 6-session crypto plan
    ├── 03-llm-project.md            ← detailed 9-phase LLM plan
    ├── 04-glossary.md               ← every tool/concept explained
    ├── context-for-agent.md         ← THIS FILE
    └── progress.md                  ← session-by-session log
```

---

## Session 1 — What needs to be built next

**Goal:** A local Kubernetes cluster with Kafka running, and a Python `trades` service producing live Kraken BTC trades to a Kafka topic. Open Kafka UI in the browser and see live messages flowing.

**Steps:**
1. Create kind cluster with port mappings (`deployments/dev/kind/`)
2. Deploy Kafka + Kafka UI via Helm (`deployments/dev/kafka/`)
3. Write `services/trades/` Python service
4. Verify live trades appear in Kafka UI at `http://localhost:8182`

**New files to create:**
```
deployments/
└── dev/
    ├── kind/
    │   ├── create_cluster.sh
    │   └── kind-with-portmapping.yaml
    └── kafka/
        ├── install_kafka.sh
        └── install_kafka_ui.sh
services/
└── trades/
    ├── pyproject.toml
    ├── README.md
    └── src/trades/
        ├── __init__.py
        ├── main.py
        ├── kraken_api.py
        ├── kafka_producer.py
        └── schemas.py
```

**Concepts the user should learn in Session 1:**
- Kubernetes pods, services, deployments, namespaces
- What Helm does and how `helm install` works
- What `kubectl port-forward` does and why it's needed
- Kafka topics, producers, partitions
- Async WebSocket clients in Python
- pydantic-settings for config (env vars instead of hardcoded values)

---

## Reference material

- **Master repo** (instructor's reference, read-only): `C:\Users\HP\Downloads\Real-World-ML-Project-master\`
- **Original reference copy**: `C:\Users\HP\Downloads\Real-World-ML-Project-reference\`
- These are on the Windows filesystem. To read them from WSL: `/mnt/c/Users/HP/Downloads/Real-World-ML-Project-master/`

---

## Working principles (always follow these)

1. **This is a learning activity** — explain every new concept before using it
2. **Explain from first principles** — don't assume knowledge of K8s, Kafka, etc.
3. **Don't skip steps** — even if something could be automated, the user should type it and understand it
4. **Always end a session with a green build** — no broken code left overnight
5. **One commit per session minimum** — message format: `session N: <what you did>`
6. **Update `docs/progress.md`** at the end of every session
7. **Tear down kind cluster between sessions** — `kind delete cluster` saves RAM
8. **Tests before (or alongside) code** — unit tests, especially for stream processing logic
9. **No magic** — if a command does something, explain what it does before running it

---

## What NOT to do

- Do not run commands on Windows PowerShell (use WSL bash)
- Do not keep the project at `/mnt/c/...` in WSL (slow; use `~/projects/...`)
- Do not add devcontainer back (we've moved to WSL2 approach)
- Do not skip to Session 2 before Session 1's "definition of done" is met
- Do not install tools globally with pip (use `uv` or `uv tool install`)
