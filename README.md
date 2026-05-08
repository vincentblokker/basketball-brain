# Basketball Brain

Productie-RAG over Nederlandse basketbal-bronnen (NBB-regels, FIBA, talentontwikkeling, coachfilosofie). ADA-eindopdracht en tegelijk de eerste ClubDuty AI-feature. Open-source, geen Microsoft-stack.

Het doel: een snelle, betrouwbare vraagbaak voor coaches, scheidsrechters en spelers — met traceerbare citaten naar de oorspronkelijke regelteksten en methodieken. Antwoorden in het Nederlands, retrieval over bronnen die anders verspreid en ontoegankelijk zijn.

## Stack

**Backend (`api/`)**
- FastAPI — async API-laag
- LangChain — orchestration + text splitters
- ChromaDB — vector store (lokaal-eerst, geen managed service)
- bge-m3 — multilingual embeddings (sterk op Nederlands)
- OpenRouter — LLM-gateway (Claude Sonnet voor reasoning, Haiku voor cheap calls; model-swap via env-var)
- Ragas — eval harness

**Frontend (`web/`, komt later)**
- Next.js 15 (App Router)
- Tailwind 4 + shadcn/ui

**Infra**
- Hetzner VPS + Caddy (reverse proxy, auto-TLS)
- Geen Azure, geen Vercel-lock-in

## Quickstart

```bash
cd api
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

API draaien (komt in volgende task):
```bash
uvicorn app.main:app --reload
```

## Repo-layout

- `api/` — Python backend, ingest pipeline, retrieval, generation, eval
- `infra/caddy/` — Caddyfile en deploy-config
- `scripts/` — losse helpers (ingest-runs, eval-runs)
- `docs/` — architectuur en design notes

## Author

Vincent Blokker — `vincentblokker@gmail.com`

## License

MIT — zie [LICENSE](./LICENSE).
