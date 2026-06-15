# Multi-stage Dockerfile for the predictor service.
# Uses pip install from pyproject.toml (same pattern as other services).

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
CMD ["python", "-m", "predictor"]
