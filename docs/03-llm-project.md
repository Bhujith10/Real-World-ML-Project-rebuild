# LLM Project — AI Research Workspace

**Total effort:** ~80 hours across 9 phases (~18 sessions)
**End state:** A multi-agent research assistant on Kubernetes that does RAG + GraphRAG, uses a self-hosted fine-tuned LLM, behind an API gateway with rate limits, with full observability.

## What it does (user-facing)

You give it a research topic. It:

1. Searches arXiv, Hacker News, and tech blogs for relevant content.
2. Retrieves and ranks documents using hybrid (dense + sparse) search.
3. Builds a knowledge graph of papers, authors, and concepts (GraphRAG).
4. Multiple specialized agents (researcher, critic, synthesizer) collaborate to produce a structured brief.
5. Lets you chat with the brief, drill into citations, and request follow-ups.
6. Uses a fine-tuned classifier (LoRA on a 7–8B base model) to score paper quality.

Resume bullet:

> Built an AI Research Workspace on Kubernetes: multi-agent system (LangGraph) with hybrid RAG (Qdrant + BGE re-ranking, evaluated with Ragas), GraphRAG (Neo4j), a fine-tuned LoRA classifier on Llama-3.1-8B served via vLLM with quantization, Kong API gateway with token-bucket rate limiting, and full observability via Langfuse + Prometheus + Grafana.

## Architecture (target end state)

```
                    ┌──────────────────────────────────┐
   Browser ───────▶ │   Kong API Gateway               │
                    │   (auth, rate limit, routing)    │
                    └──────────────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
      │   research   │      │   chat-api   │      │  ingestion   │
      │   service    │      │   service    │      │   service    │
      │  (LangGraph  │      │  (streaming  │      │  (arXiv,     │
      │   agents)    │      │   responses) │      │   crawl)     │
      └──────────────┘      └──────────────┘      └──────────────┘
              │                     │                     │
              │                     │                     ▼
              │                     │              ┌──────────────┐
              │                     │              │  embeddings  │
              │                     │              │   pipeline   │
              │                     │              └──────────────┘
              │                     │                     │
              ▼                     ▼                     ▼
      ┌─────────────────────────────────────────────────────────┐
      │   Storage layer                                         │
      │   ┌──────────┐  ┌──────────┐  ┌──────────┐ ┌─────────┐ │
      │   │  Qdrant  │  │  Neo4j   │  │ Postgres │ │ Object  │ │
      │   │ (vectors)│  │  (graph) │  │ (meta)   │ │ store   │ │
      │   └──────────┘  └──────────┘  └──────────┘ └─────────┘ │
      └─────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │  vLLM serving    │
                          │  (fine-tuned     │
                          │   Llama-3.1-8B   │
                          │   + quantized)   │
                          └──────────────────┘

      Cross-cutting: Langfuse (LLM traces) + Prometheus + Grafana + Loki
```

## Tech stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| LLM clients | OpenAI, Anthropic SDKs (cloud); vLLM (self-hosted) |
| Structured output | Instructor + Pydantic |
| Agent framework | LangGraph |
| LLM observability | Langfuse |
| Vector DB | Qdrant |
| Embeddings | BGE-large-en (open) + Cohere re-ranker |
| Graph DB | Neo4j |
| Fine-tuning | Hugging Face TRL + PEFT (LoRA/QLoRA) |
| GPU compute | RunPod or Modal (rented A100 for ~hours) |
| Model serving | vLLM with AWQ/GPTQ quantization |
| API gateway | Kong (open source) |
| Rate limiting | Kong plugin (token bucket) |
| Auth | Kong + JWT |
| Container | Docker (reusing crypto MVP patterns) |
| Orchestration | Kubernetes via `kind` |
| CI/CD | GitHub Actions |
| Observability | Prometheus + Grafana + Loki + Langfuse |

## Phases

### Phase 1 — Foundations (2 sessions, 8–10 hrs)

- FastAPI service skeleton with health/readiness endpoints
- Pydantic models, structured logging, settings via `pydantic-settings`
- Dockerfile + K8s deployment to kind (reuse crypto MVP patterns)
- Tests with pytest + httpx
- Pre-commit + ruff + mypy

**DoD:** `curl http://localhost:8000/health` returns 200 from a pod in your cluster.

---

### Phase 2 — LLM basics (2 sessions, 8–10 hrs)

- Provider-agnostic LLM client wrapper (OpenAI + Anthropic)
- Structured output with Instructor (JSON schemas via Pydantic)
- Streaming responses (server-sent events)
- Eval harness: pytest-based golden-set evaluation
- Cost tracking, latency tracking, retry logic with exponential backoff

**DoD:** `pytest tests/eval/` runs your golden set and prints pass/fail per case with cost/latency.

---

### Phase 3 — RAG (3 sessions, 12–14 hrs)

- Deploy Qdrant to kind cluster (Helm)
- Ingestion pipeline: chunk documents, embed with BGE, upsert to Qdrant
- Hybrid retrieval: dense (vector) + sparse (BM25 via tantivy)
- Re-ranking with Cohere or BGE-reranker
- Ragas evaluation (faithfulness, answer relevancy, context precision)
- Chunking strategies: fixed-size vs semantic vs hierarchical

**DoD:** Ask a question, get an answer with cited chunks; Ragas score above a threshold on a golden eval set.

---

### Phase 4 — Agents (3 sessions, 12–14 hrs)

- LangGraph multi-agent system: researcher, critic, synthesizer
- Tool use: search, retrieve, calculate, code-exec
- Retries, fallbacks, circuit breakers
- Langfuse traces for every LLM call (with parent/child spans)
- Agent evaluation: success rate on a benchmark task set

**DoD:** Agent completes a research task end-to-end; full trace visible in Langfuse with token counts.

---

### Phase 5 — GraphRAG (2 sessions, 8–10 hrs)

- Deploy Neo4j to cluster
- Entity + relationship extraction from documents (LLM-driven)
- Build graph: papers, authors, concepts, citations
- Cypher queries combined with vector retrieval (hybrid graph + vector)
- Compare answer quality: RAG vs GraphRAG vs RAG+GraphRAG

**DoD:** A query like "what concepts connect papers X and Y" returns a path through the graph.

---

### Phase 6 — Fine-tuning (2 sessions, 10–12 hrs)

- Dataset curation: a paper-quality classification task (good/mediocre/spam)
- Rent A100 on RunPod for ~3–6 hours
- LoRA fine-tune Llama-3.1-8B-Instruct or Qwen-2.5-7B
- Push adapters to Hugging Face Hub
- Eval against base model + GPT-4o on held-out set

**DoD:** Adapter weights on HF Hub; eval shows fine-tuned model beats base on the task.

---

### Phase 7 — LLM serving (2 sessions, 8–10 hrs)

- vLLM deployed to cluster (CPU-only inference for now, or rented GPU pod)
- Quantization: AWQ or GPTQ
- A/B testing: percentage routing between two model versions
- Canary deploy: rolling update with rollback on error rate spike

**DoD:** Hit `/v1/completions` on your vLLM endpoint; latency + tokens/sec visible in Grafana.

---

### Phase 8 — Production gateway (2 sessions, 8–10 hrs)

- Kong deployed to cluster
- Routes: `/api/v1/*` → research service, `/v1/*` → vLLM, etc.
- Rate limiting: token-bucket per user/API key
- Auth: JWT issuer + verifier
- Prometheus + Grafana + Loki stack deployed
- Per-service SLOs (e.g., p95 latency < 2s)

**DoD:** Hammer the endpoint with `hey` or `k6`; rate limiter kicks in; latency dashboard shows SLO compliance.

---

### Phase 9 — Frontend + capstone (1 session, 4–5 hrs)

- Minimal Streamlit UI (or Next.js if motivated)
- Polish READMEs, architecture diagrams, deploy instructions
- Record 3-min demo video
- Tag `v1.0.0`, push, post to LinkedIn

**DoD:** Demo link works on a clean machine. Resume bullet sounds great.

---

## Cost budget (out-of-pocket)

| Item | Estimated cost |
|---|---|
| OpenAI/Anthropic API for dev + eval | $30–50 |
| RunPod A100 for fine-tuning (4–8 hrs) | $10–20 |
| Cohere re-ranker (free tier mostly) | $0–5 |
| Domain + hosting (optional, for demo URL) | $10–20 |
| **Total** | **~$50–100** |

Keep API keys in `.env.local` (gitignored). Use cheap models (gpt-4o-mini, claude-haiku) for development; only use big models for final eval.

## Skill outcomes

After Phase 9 you'll be able to:

- Design and ship an LLM-powered system end-to-end
- Choose between RAG, GraphRAG, fine-tuning, and prompting based on the problem
- Set up evals before shipping prompts (the #1 sign of a serious AI engineer)
- Self-host an LLM with quantization and serve it behind a gateway
- Implement rate limiting, auth, observability for any service
- Talk credibly in interviews about LangGraph, Qdrant, Neo4j, vLLM, Kong, Langfuse
