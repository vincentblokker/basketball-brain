# Infra — Basketball Brain

Docker-compose stack for [brain.clubduty.app](https://brain.clubduty.app) running on
Hetzner CAX21. Three services:

- `api` — FastAPI backend (port 8000, internal only)
- `web` — Next.js standalone server (port 3000, internal only)
- `caddy` — reverse proxy on 80/443 with auto-HTTPS via Let's Encrypt

## Routing

Caddy terminates TLS on `brain.clubduty.app` and routes:

- `/api/*` → `api:8000` (the `/api` prefix is **stripped** before proxy, so the
  backend sees `/health`, `/query`, etc.)
- everything else → `web:3000`

The frontend is built with `NEXT_PUBLIC_API_BASE=https://brain.clubduty.app/api`
so client calls hit the backend through Caddy.

## Build context

The `api` service builds from the **repo root** (`context: ..`) instead of
`../api` so the image can include both `api/` and `scripts/` directories. The
Dockerfile uses `api/`-prefixed COPY paths and creates a `/app/api` symlink so
that `scripts/ingest_all.py` resolves its hardcoded `repo_root / "api"` paths
correctly inside the container.

The `web` service builds normally from `../web`.

## Deploy to Hetzner (ServerCAX21)

### Prereqs

- Server has Docker + docker-compose installed
  (`apt install docker.io docker-compose-plugin`)
- DNS A-record `brain.clubduty.app` → server IP, propagated
- OpenRouter API key

### First deploy

```bash
ssh user@your-hetzner-ip

# Clone the repo
mkdir -p /opt/basketball-brain && cd /opt/basketball-brain
git clone https://github.com/vincentblokker/basketball-brain .

# Create env file from template, fill in OPENROUTER_API_KEY
cp api/.env.example api/.env
nano api/.env  # add OPENROUTER_API_KEY=sk-or-...

# Build and start (first run takes 5-10 min for bge-m3 download in api container)
cd infra
docker compose up -d --build

# Once api is healthy, run one-shot ingest
docker compose exec api python scripts/ingest_all.py

# Verify
curl https://brain.clubduty.app/api/health
# → {"status":"ok"}
```

### Subsequent deploys (after code push to main)

```bash
cd /opt/basketball-brain
git pull
cd infra
docker compose up -d --build
```

### Re-ingest

```bash
docker compose exec api python scripts/ingest_all.py
```

### Logs

```bash
docker compose logs -f api
docker compose logs -f web
docker compose logs -f caddy
```

### Wipe and re-ingest from scratch

```bash
docker compose down
docker volume rm infra_chroma_data
docker compose up -d --build
docker compose exec api python scripts/ingest_all.py
```
