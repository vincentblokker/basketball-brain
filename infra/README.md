# Infra — Basketball Brain

Docker-compose stack for [brain.clubduty.app](https://brain.clubduty.app) running on
the existing `clubduty-marketing-prod` server (Hetzner ARM64). Two services:

- `api` — FastAPI backend, bound to `127.0.0.1:8000`
- `web` — Next.js standalone server, bound to `127.0.0.1:3000`

**No Caddy in docker-compose.** This server already runs `caddy.service` (systemd)
to serve the marketing site on `clubduty.app`. We integrate by adding a site
block to the host Caddyfile.

## Routing (via host Caddy)

Host Caddy terminates TLS on `brain.clubduty.app` and routes:

- `/api/*` → `127.0.0.1:8000` (the `/api` prefix is **stripped** before proxy, so the
  backend sees `/health`, `/query`, etc.)
- everything else → `127.0.0.1:3000`

The frontend is built with `NEXT_PUBLIC_API_BASE=https://brain.clubduty.app/api`
so client calls hit the backend through Caddy.

## Host Caddyfile snippet

Add to `/etc/caddy/Caddyfile` (alongside the existing `clubduty.app` block):

```
brain.clubduty.app {
    encode gzip zstd

    handle_path /api/* {
        reverse_proxy 127.0.0.1:8000 {
            health_uri /health
        }
    }

    handle {
        reverse_proxy 127.0.0.1:3000
    }

    log {
        output file /var/log/caddy/brain.clubduty.app.log
        format console
    }
}
```

Then: `sudo systemctl reload caddy`. Let's Encrypt cert is issued automatically
on first request.

## Build context

The `api` service builds from the **repo root** (`context: ..`) instead of
`../api` so the image can include both `api/` and `scripts/` directories. The
Dockerfile uses `api/`-prefixed COPY paths and creates a `/app/api` symlink so
that `scripts/ingest_all.py` resolves its hardcoded `repo_root / "api"` paths
correctly inside the container.

The `web` service builds normally from `../web`.

## Deploy

### Prereqs

- Docker + docker-compose plugin installed (`sudo apt install docker.io docker-compose-plugin`)
- User in `docker` group (`sudo usermod -aG docker $USER` then re-login)
- DNS A-record `brain.clubduty.app` → server IP, propagated
- OpenRouter API key
- Host Caddyfile already updated (see snippet above)

### First deploy

```bash
ssh clubduty-marketing
sudo mkdir -p /opt/basketball-brain && sudo chown $USER /opt/basketball-brain
cd /opt/basketball-brain
git clone https://github.com/vincentblokker/basketball-brain .

# Create env file from template, fill in OPENROUTER_API_KEY
cp api/.env.example api/.env
nano api/.env  # add OPENROUTER_API_KEY=sk-or-...

# Build and start (first run takes 10-20 min on ARM64 — bge-m3 download + build)
cd infra
docker compose up -d --build

# Once api is healthy, run one-shot ingest (after content downloaded too)
docker compose exec api python scripts/ingest_all.py

# Verify
curl https://brain.clubduty.app/api/health
# → {"status":"ok"}
```

### Subsequent deploys

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
sudo journalctl -fu caddy   # host Caddy logs
```

### Wipe ChromaDB and re-ingest from scratch

```bash
docker compose down
docker volume rm infra_chroma_data
docker compose up -d --build
docker compose exec api python scripts/ingest_all.py
```
