# Multi-stage Dockerfile for the technical_indicators service
# Stage 1: Build — install dependencies with pip
# Stage 2: Runtime — lean image with only what's needed

FROM python:3.13-slim AS builder

WORKDIR /app

# Install dependencies first (cached if pyproject.toml unchanged)
COPY pyproject.toml ./
COPY src/ src/
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install .

# --- Runtime stage ---
FROM python:3.13-slim

WORKDIR /app

# Copy only the virtual environment and source code
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Put the venv's Python on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Run the service
CMD ["python", "-m", "technical_indicators"]
