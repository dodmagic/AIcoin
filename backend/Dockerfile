# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1: build dependencies into an isolated prefix for a slim final image.
# Build context is the repository root so the `backend` package is available.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /install

# Install dependencies first to maximise Docker layer caching.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --prefix=/install/deps -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: runtime image — non-root, slim, with a healthcheck.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# curl is used by the container HEALTHCHECK and docker-compose healthchecks.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Run as a dedicated non-root user.
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app

# Bring in the pre-built dependencies, then the application code.
COPY --from=builder /install/deps /usr/local
COPY backend ./backend

# The runtime container doesn't install packages, so drop build-only packaging
# tools to keep the image smaller and avoid shipping vulnerable vendored copies.
RUN rm -rf \
      /usr/local/lib/python3.11/site-packages/pkg_resources \
      /usr/local/lib/python3.11/site-packages/setuptools \
      /usr/local/lib/python3.11/site-packages/setuptools-*.dist-info \
      /usr/local/lib/python3.11/site-packages/wheel \
      /usr/local/lib/python3.11/site-packages/wheel-*.dist-info \
      /usr/local/bin/wheel

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
