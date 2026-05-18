# src/backend/Dockerfile
# Multi-stage build for smaller image and reduced attack surface

# ─── Stage 1: Builder ───
# Use explicit bookworm tag for latest Debian 12 security patches
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY requirements.txt .
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN pip install --no-cache-dir -r requirements.txt -i ${PIP_INDEX_URL} --timeout 120

# ─── Stage 2: Runtime ───
FROM python:3.11-slim-bookworm AS runtime

# Patch available system packages (Hadolint allows upgrade, not dist-upgrade)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy application code
COPY app.py .
COPY main.py .
COPY schemas.py .
COPY routes/ ./routes/
COPY utils/ ./utils/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Create non-root user and fix ownership
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Healthcheck using the /ready endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/ready')" || exit 1

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "--graceful-timeout", "30", "--timeout", "120", "main:app"]
