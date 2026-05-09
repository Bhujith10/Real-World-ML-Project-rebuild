# Roadmap

## Why this project exists

To learn modern AI/ML engineering by building two production-grade systems end to end:

1. A **real-time data engineering + ML system** (crypto prediction MVP) — gives you Kafka, Kubernetes, Docker, MLflow, streaming SQL, CI/CD muscle memory.
2. An **LLM/AI engineering system** (AI Research Workspace) — gives you RAG, GraphRAG, agents, fine-tuning, LLM serving, API gateway, rate limiting.

Combined, these two projects cover the skill set of a 2025-era AI Engineer / ML Engineer.

## Stated learning goals

- Agents (multi-agent orchestration, tool use)
- LLM workflows (chains, structured output, function calling)
- RAG (vector DB, embeddings, hybrid retrieval, evaluation)
- GraphRAG (knowledge graphs)
- Fine-tuning LLMs (LoRA, QLoRA)
- Deploying LLMs (vLLM, quantization)
- API gateway, rate limiting, auth
- Production best practices: CI/CD, observability, drift monitoring
- Best practices for deploying ML models

## End state (after both projects)

You will have:

1. **Two GitHub repos**, both runnable end-to-end on a clean machine.
2. **Two demo videos** (~3 min each) showing the systems running.
3. **Two READMEs** that an interviewer can read in 2 minutes and understand the architecture.
4. **A single resume bullet for each project** that's specific, technical, and verifiable.

Sample bullets:

> Built a real-time crypto price prediction system: 5 microservices on Kubernetes processing live Kraken WebSocket trades through Kafka + Quixstreams + RisingWave streaming SQL feature store + MLflow-tracked XGBoost. CI/CD with GitHub Actions, observability with Grafana.

> Built an AI Research Workspace: multi-agent system on Kubernetes combining RAG (Qdrant + hybrid retrieval + Ragas eval), GraphRAG (Neo4j), a fine-tuned classifier (LoRA on Llama-3.1-8B), self-hosted vLLM serving with quantization, Kong API gateway with rate limiting, and full observability (Langfuse + Prometheus + Grafana).

## Timeline

| Phase | Sessions | Effort | Calendar @ 1.5–2 hrs/day |
|---|---|---|---|
| Session 0 (env) | 1 | 3–5 hrs | 2–3 days |
| Crypto MVP (S1–S6) | 6 | ~30 hrs | 4–5 weeks |
| Pivot design | 1 | 2–3 hrs | 1–2 days |
| LLM project (Phase 1–9) | ~18 | ~80 hrs | 11–13 weeks |
| **Total** | **~26 sessions** | **~115 hrs** | **~5 months** |

## Working principles

1. **Always finish a session in one sitting.** Stopping mid-session destroys momentum.
2. **End every session with a green build.** Don't leave broken code overnight.
3. **One commit per session minimum**, with a useful message: `session N: <what you did>`.
4. **Update `progress.md` at the end of every session** — 3 lines max.
5. **Tear down `kind` cluster between sessions.** `kind delete cluster` saves 4–8 GB RAM.
6. **Tests before code when possible.** A failing test you write first is the best teaching tool.
7. **Don't skip writing READMEs.** Future-you in 3 weeks will need them more than you think.

## Two-project structure on disk

```
C:\Users\HP\Downloads\
├── Real-World-ML-Project-master/      # Instructor's repo (read-only reference)
├── Real-World-ML-Project-reference/   # Your prior course copy (read-only reference)
└── Real-World-ML-Project-rebuild/     # ← active work (this folder)
    ├── docs/                          # ← this plan
    ├── services/                      # crypto MVP services live here
    ├── deployments/                   # K8s manifests
    └── (later) llm-workspace/         # LLM project lives here
```

## What we're explicitly NOT doing in the crypto MVP

(To stay under 30 hrs. Skipped on purpose, not by accident.)

- News + news-sentiment services (better covered in LLM project)
- Cloud K8s deployment (cost + complexity)
- Hourly retraining cron jobs
- Helm charts (raw YAML / kustomize is enough)
- Drift monitoring (covered in LLM project)
- Backfill pipeline
- Risk/portfolio management

## What success looks like at each milestone

- **End of Session 0:** type `kubectl version` and `uv --version` in WSL terminal; both work.
- **End of Crypto S1:** open Kafka UI in browser, see live BTC trades flowing.
- **End of Crypto S6:** open Grafana, see live candles + predictions overlaid; CI runs on every push.
- **End of LLM Phase 3:** ask a question, RAG returns relevant document chunks with eval scores.
- **End of LLM Phase 7:** your fine-tuned model serves via vLLM in cluster, behind API gateway with rate limits.
- **End of LLM Phase 9:** record a demo video, push final commit, update LinkedIn.
