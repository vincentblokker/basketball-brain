FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install uv (project uses uv for fast pip-compatible installs)
RUN pip install --no-cache-dir uv

# Copy dependency manifest first to leverage Docker layer caching.
# Build context is the repo root (see infra/docker-compose.yml), so paths
# are prefixed with api/ for the api package and scripts/ for the ingest CLI.
COPY api/pyproject.toml ./
RUN uv pip install --system --no-cache -e .

# Copy app and pre-downloaded raw data (sources.json + Vincent's downloaded PDFs)
COPY api/app ./app
COPY api/data/raw ./data/raw

# Copy ingest scripts so `docker compose exec api python scripts/ingest_all.py` works.
# scripts/ingest_all.py expects to live one dir up from `api/` in the repo,
# but inside the container we flatten to /app/{app,data,scripts}. The script
# uses Path(__file__).resolve().parent.parent / "api" to locate the app, which
# would resolve to /app -- so we keep the layout compatible by symlinking
# /app/api -> /app for the script's path-resolution to land correctly.
COPY scripts ./scripts
RUN ln -s /app /app/api

# Create chroma persistence dir (mounted as volume in compose)
RUN mkdir -p ./chroma
# Page-thumbnail dir (bind-mounted in compose)
RUN mkdir -p ./data/pages

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
