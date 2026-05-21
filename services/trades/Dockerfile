# Multi-stage Dockerfile for the trades service.
#
# Stage 1 (builder): install dependencies using uv
# Stage 2 (runtime): copy only what's needed to run — keeps image small
#
# Why multi-stage?
# - Build tools (compilers, uv itself) aren't needed at runtime
# - Smaller image = faster deploys, less attack surface

FROM python:3.13-slim AS builder

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (better Docker layer caching)
COPY pyproject.toml uv.lock* ./
COPY src/ src/

# Install dependencies into the system Python (no venv needed in container)
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

# --- Runtime stage ---
FROM python:3.13-slim

WORKDIR /app

# Copy installed packages and source from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Put the venv's Python on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Run the service
CMD ["python", "-m", "trades.main"]
