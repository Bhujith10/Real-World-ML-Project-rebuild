# Glossary

A one-line explanation for every tool/concept you'll meet in these projects. Keep this open in a tab.

## Operating system & shells

| Term | Meaning |
|---|---|
| **WSL2** | Windows Subsystem for Linux 2 — runs a real Linux kernel inside Windows. We work inside Ubuntu via WSL2. |
| **bash** | The default Linux shell. Most scripts in this project are bash. |
| **Ubuntu 24.04** | Our Linux distribution running inside WSL2. |
| **`apt`** | Ubuntu's package manager. `sudo apt install <pkg>`. |

## Containers & orchestration

| Term | Meaning |
|---|---|
| **Docker** | Tool to package an app + its dependencies into a portable image; runs as containers. |
| **Container** | A running instance of an image. Lightweight, isolated, ephemeral. |
| **Image** | A read-only blueprint built from a `Dockerfile`. |
| **Dockerfile** | Recipe for building an image. |
| **GHCR** | GitHub Container Registry — where we push our images. |
| **Multi-stage build** | A Dockerfile pattern where you build in one stage and copy only artifacts to a slim final stage. Reduces image size dramatically. |
| **Kubernetes (K8s)** | Platform that orchestrates containers across machines: scheduling, healing, scaling, networking. |
| **`kubectl`** | The CLI for talking to a Kubernetes cluster. |
| **`kind`** | "Kubernetes IN Docker" — runs a K8s cluster as Docker containers on your laptop. |
| **Pod** | Smallest deployable unit in K8s. Wraps one or more containers that share networking and storage. |
| **Deployment** | A K8s object describing how to run a stateless app: replicas, image, resources. |
| **Service** | A K8s object that gives Pods a stable DNS name + load balancer. |
| **Secret** | Encrypted key-value store for passwords, API keys. |
| **ConfigMap** | Plain-text key-value store for non-secret config. |
| **Helm** | Package manager for K8s — installs apps from charts (e.g., Kafka, RisingWave). |
| **Helm chart** | Templated set of K8s YAMLs you can install with `helm install`. |
| **`kustomize`** | Tool for layering YAML overrides per environment (dev/prod) without templates. |
| **`k9s`** | Terminal UI for navigating a K8s cluster. |

## Python tooling

| Term | Meaning |
|---|---|
| **`uv`** | Modern Python package + project manager (replaces pip, pip-tools, virtualenv). |
| **uv workspace** | A monorepo pattern where multiple Python packages live in one repo with a shared lockfile. |
| **`pyproject.toml`** | Standard Python project metadata file (dependencies, build system). |
| **`mise`** | Tool version manager — pins exact versions of `kubectl`, `helm`, etc. per project. |
| **`pydantic`** | Library for data validation via type hints. The de facto standard for Python data models. |
| **`pydantic-settings`** | Loads config from env vars/files into Pydantic models. |
| **`ruff`** | Fast Python linter + formatter. Replaces black, isort, flake8. |
| **`pre-commit`** | Runs hooks (like ruff) before every git commit. |
| **`direnv`** | Auto-loads env vars when you `cd` into a folder with `.envrc`. |

## Streaming & data

| Term | Meaning |
|---|---|
| **Apache Kafka** | Distributed event streaming platform — producers write events to topics, consumers read them. |
| **Topic** | A named, partitioned log of messages in Kafka. |
| **Producer / Consumer** | Apps that write to / read from Kafka topics. |
| **Strimzi** | Kubernetes operator that deploys Kafka. Used in this project. |
| **Quixstreams** | Python library for stream processing on Kafka (windowing, joins, aggregations). |
| **Tumbling window** | Non-overlapping fixed-size time buckets (e.g., 1-min OHLCV). |
| **Hopping window** | Overlapping windows that advance by a step smaller than their size. |
| **Sliding window** | Window that recomputes on every event arrival. |
| **Watermark** | A timestamp signaling "no events older than this will arrive" — used to close windows. |
| **RisingWave** | Streaming database — Postgres-compatible but tables are continuously updated materialized views over Kafka topics. |
| **Materialized view** | A SQL query whose result is cached and updated incrementally. |
| **Feature store** | A system that stores ML features for both training (offline) and inference (online), preventing online-offline skew. |
| **Online-offline skew** | Bug where features used at inference differ from those used at training, silently degrading model quality. |

## ML & MLOps

| Term | Meaning |
|---|---|
| **MLflow** | Platform for tracking experiments, registering models, and serving them. |
| **Model registry** | Versioned store of trained models with metadata. |
| **XGBoost** | Gradient-boosted tree library. Great for tabular data. |
| **Train/serve parity** | Property that the same code/data is used for training and serving features. Critical to avoid silent failures. |
| **Drift detection** | Monitoring whether the data your model sees in production differs from what it was trained on. |
| **A/B testing** | Routing a percentage of traffic to a new version to measure impact. |
| **Canary deploy** | Rolling out a new version to a small fraction first, expanding if metrics are good. |

## LLMs & AI engineering

| Term | Meaning |
|---|---|
| **LLM** | Large Language Model (e.g., GPT-4, Claude, Llama). |
| **Embedding** | A dense vector representation of text used for semantic search. |
| **Vector database** | DB optimized for nearest-neighbor search over embeddings (e.g., Qdrant, Pinecone). |
| **RAG** | Retrieval-Augmented Generation — fetch relevant docs, stuff them into the prompt. |
| **Hybrid retrieval** | Combining dense (vector) and sparse (keyword/BM25) search for better recall. |
| **Re-ranker** | A second-stage model that re-scores retrieved candidates for relevance. |
| **GraphRAG** | RAG variant that retrieves from a knowledge graph instead of (or in addition to) a vector store. |
| **Knowledge graph** | A graph of entities (nodes) and relationships (edges) extracted from a corpus. |
| **Neo4j** | The most popular graph database; uses Cypher query language. |
| **Cypher** | Neo4j's SQL-like query language for graphs. |
| **Agent** | An LLM that can take actions via tools (search, code, API calls), often in a loop. |
| **LangGraph** | Library for building stateful, multi-agent LLM applications as directed graphs. |
| **Tool use / function calling** | LLM capability to emit structured calls to external functions. |
| **Structured output** | Forcing an LLM to respond in a specific schema (JSON), via libraries like Instructor. |
| **Instructor** | Python library that wraps LLM SDKs to return Pydantic models. |
| **Eval / golden set** | A curated set of input-output pairs you test prompts/models against in CI. |
| **Ragas** | Library for evaluating RAG pipelines (faithfulness, relevancy, etc.). |
| **Langfuse** | Observability tool for LLM apps — traces every call with cost, latency, parent/child spans. |
| **Fine-tuning** | Continuing to train a pretrained model on your domain data. |
| **LoRA** | Low-Rank Adaptation — fine-tune by only training small adapter matrices. ~100x cheaper than full fine-tune. |
| **QLoRA** | LoRA + 4-bit quantized base model. Fits 7–13B fine-tunes on a single 24GB GPU. |
| **PEFT** | Hugging Face library implementing LoRA, prefix tuning, etc. |
| **TRL** | HF Transformer Reinforcement Learning — wraps SFT, DPO, PPO. |
| **vLLM** | Open-source LLM serving engine with PagedAttention; fast batched inference. |
| **Quantization** | Compressing model weights (FP16 → INT8/INT4) for faster, smaller inference. |
| **AWQ / GPTQ** | Two popular quantization methods for LLMs. |
| **API gateway** | A reverse proxy that handles auth, routing, rate limiting for many services behind it. |
| **Kong** | Open-source API gateway, K8s-native. |
| **Rate limiting** | Capping how many requests a client can make per time window. |
| **Token bucket** | A common rate-limiting algorithm; tokens replenish at a fixed rate, each request consumes one. |
| **Observability** | The discipline of metrics + logs + traces — so you can debug production. |
| **Prometheus** | Metrics collection + storage. |
| **Grafana** | Dashboards on top of Prometheus (and many other sources). |
| **Loki** | Log aggregation, by Grafana Labs. |

## Git & GitHub

| Term | Meaning |
|---|---|
| **PAT** | Personal Access Token — used as password when pushing over HTTPS. |
| **GitHub Actions** | GitHub's built-in CI/CD. YAML workflows in `.github/workflows/`. |
| **Workflow** | A YAML file describing CI/CD steps. |
| **Action** | A reusable building block in a workflow (e.g., `actions/checkout@v4`). |
