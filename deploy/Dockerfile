# =============================================================================
# quantum-price-inference — Dockerfile
#
# Multi-stage build:
#   Stage 1 (builder) — installs dependencies into an isolated venv via uv
#   Stage 2 (runtime) — copies only the venv + source; no build tools
#
# Build:
#   docker build -f deploy/Dockerfile -t quantum-price-inference:latest .
#
# Run:
#   docker run --rm -p 8000:8000 quantum-price-inference:latest
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — builder
# ---------------------------------------------------------------------------
# python:3.13-slim matches the development environment (Python 3.13.7).
# Pinned to bookworm for a stable Debian base.
FROM python:3.13-slim-bookworm AS builder

# Pin uv to the same version used in development for reproducibility.
RUN pip install --no-cache-dir uv==0.11.3

WORKDIR /app

# Copy dependency manifests first — Docker layer cache is reused when only
# source code changes, not when deps change.
COPY pyproject.toml uv.lock LICENSE README.md ./

# Install core runtime deps only (no dev tools, no notebook extras).
# --frozen ensures the lock file is never silently regenerated.
RUN uv sync --no-dev --frozen

# ---------------------------------------------------------------------------
# Stage 2 — runtime
# ---------------------------------------------------------------------------
FROM python:3.13-slim-bookworm

# Install curl for the HEALTHCHECK.  Kept minimal with --no-install-recommends.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security hardening.
RUN addgroup --system qpi && adduser --system --ingroup qpi qpi

WORKDIR /app

# Copy the pre-built venv from the builder stage.
COPY --from=builder --chown=qpi:qpi /app/.venv /app/.venv

# Copy application source.
COPY --chown=qpi:qpi quantum_price_inference/ ./quantum_price_inference/
COPY --chown=qpi:qpi api/ ./api/

# Put the venv on PATH so `uvicorn` and `python` resolve from it.
ENV PATH="/app/.venv/bin:$PATH"

# Runtime configuration — all values are overridable via environment variables.
# Once api/config.py (Wave 3.3) is implemented these will be read automatically.
# Workers: 2 * CPU_count + 1 is the uvicorn rule of thumb.
# For a 2-vCPU container use 5; for the workshop demo 2 is fine.
ENV QPI_LOG_LEVEL="INFO" \
    QPI_LOG_JSON="true" \
    QPI_WORKERS="2"

USER qpi

EXPOSE 8000

# Liveness probe — matches /health/live added in Wave 2.4.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["sh", "-c", \
     "uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers ${QPI_WORKERS}"]
