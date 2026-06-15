# Multi-stage Dockerfile for the candles service.
# Same pattern as the trades service:
#   Stage 1 (builder): install dependencies with uv
#   Stage 2 (runtime): copy only what's needed to run

FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=120

WORKDIR /app

# Install dependencies first (cached if pyproject.toml unchanged)
COPY pyproject.toml uv.lock* ./
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

# --- Runtime stage ---
FROM python:3.13-slim

WORKDIR /app

# Copy only the virtual environment and source code
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Put the venv's Python on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Run the service
CMD ["python", "-m", "candles"]
