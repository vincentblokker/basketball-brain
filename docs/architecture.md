# Architecture

Stack-keuzes, ontwerpbeslissingen, en de bewuste afwijking van de Azure-route die de cursus voorschreef.

## High-level overview

```
PDFs/HTML  →  Loader  →  Chunker  →  bge-m3 embed  →  ChromaDB
                            │              │                │
                            ▼              ▼                │
                       page PNGs       BM25 index           │
                       (static)        (in-mem)             │
                                                            │
User query  →  hybrid_retrieve  ←  ──────────────────────────┘
                    │
                    ▼
              top-k chunks
                    │
                    ▼
              Prompt + LLM (OpenRouter → Haiku/Sonnet)
                    │
                    ▼
              Antwoord + citations  →  Frontend
                                          │
                                          ▼
                                   👁 → page-thumbnail
                                   ↗ → originele PDF
```

## Component-keuzes

### Embeddings — `BAAI/bge-m3`

- **Multilingual**: getraind op 100+ talen, sterk op Nederlands. Geverifieerd in onze test-set: NL-vragen halen correct de juiste chunks uit Engelse bronnen op
- **1024-dim, FP16-friendly**: ~2 GB model, draait comfortabel op Mac M-series en op Hetzner ARM64
- **MIT-licentie**: geen vendor-lock, geen API-cost per embedding
- **Dense + sparse + multi-vector** in één model — toekomstige hybride-features open
- Alternatief overwogen: `text-embedding-3-large` (OpenAI). Minder NL-sterk, $0,13/M tokens vs gratis self-host

### Vector store — ChromaDB (PersistentClient)

- **Self-host**: één Python-dependency, geen managed service nodig
- **HNSW met cosine**: HNSW indexering geeft sub-second query op corpus van ~5K chunks
- **Metadata filtering**: `tenant_id`, `authority`, `topic`, `level` allemaal filter-baar zonder extra index
- **Migratie-pad**: schema-compatibiliteit met Qdrant en Pinecone voor later-stage scale (50K+ chunks of multi-tenant)

### Hybrid retrieval — BM25 + vector + RRF

Pure vector retrieval mist exacte termen ("artikel 4.2.1", productcodes, eigennamen). Pure BM25 mist paraphrases en semantische verwantschap. **Reciprocal Rank Fusion** combineert beide rankings:

```python
def rrf_fusion(rank_lists, weights, k=60):
    scores = {}
    for ranking, w in zip(rank_lists, weights):
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0) + w / (k + rank + 1)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
```

`k=60` is uit het [oorspronkelijke RRF-paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) (Cormack et al., 2009).

### LLM — OpenRouter als gateway

- **OpenAI-compatible API**: één SDK voor Claude/GPT/Gemini/Llama
- **Model swap via env-var**: `LLM_MODEL=anthropic/claude-haiku-4-5` ↔ `anthropic/claude-sonnet-4-6` zonder code-wijziging
- **Default Haiku 4.5**: ~$0,002 per gebonden antwoord. Sonnet voor max-quality eval-runs of premium-tier later
- **Anthropic prompt-caching passthrough**: `cache_control: ephemeral` blijft werken voor Contextual Retrieval indexing-fase (10× kostenreductie)

### Frontend — Next.js 16 + Tailwind 4 + shadcn/ui

- **Static prerender** voor /, /about, /admin — snelle first-paint, geen SSR-complexity
- **Tailwind 4 `@theme` directive**: design tokens als CSS-variabelen, automatisch gemapt naar utility classes (`bg-bg-3`, `text-fg-2`, `border-line`)
- **Dark default** met `data-theme="light"` override — basketbal court-vibe, lichte mode beschikbaar
- **Newsreader serif** voor editorial headlines (homepage, about), Inter sans voor body
- **Citation-first**: badges met locator + 👁-knop voor page-thumbnail, geen verstopte info

### Infrastructure — Hetzner ARM64 + host-Caddy + docker-compose

- **Hetzner CAX21**: ARM64 (Ampere), bestaande server die ook clubduty.nl en mondaybeat.app serveert
- **Host-Caddy**: bestaande systemd service draait al voor andere subdomeinen. We voegen een `brain.clubduty.app` block toe, geen container-Caddy-conflict
- **docker-compose**: api + web, beide met healthchecks, bind-mount voor `data/raw` en `data/pages` zodat content-uploads en thumbnails persistent zijn
- **Let's Encrypt** automatisch via Caddy — geen handmatige cert-rotation
- **No Microsoft**: geen Azure, geen Office365, geen IIS

## Vergelijking met de Azure-route uit de cursus

| Cursus (Azure) | Dit project | Argument voor de switch |
|----------------|-------------|-------------------------|
| Azure AI Search | ChromaDB | Self-host, geen vendor-lock, gratis bij dit volume |
| Azure OpenAI | OpenRouter (Anthropic) | Model-flexibiliteit, prompt-caching support, geen MS-account |
| Azure App Service | docker-compose op Hetzner | Bestaande infra, $5/mo ipv $30+, full control |
| "Use your data" no-code | FastAPI + admin-UI | Volledige controle over chunking, retrieval, prompts |
| Azure Workbooks | (gepland: Grafana) | Open source observability |

De ADA-rubric beoordeelt op:
- ✅ Production-style RAG over publieke dataset → 10 publieke FIBA/USA/Wikipedia bronnen
- ✅ Chunking + embeddings + hybrid + semantic-rerank-equivalent → BM25+vector+RRF (semantic rerank is roadmap)
- ✅ Live deployable web app → brain.clubduty.app
- ✅ Evaluation report met before/after tuning → 3 iteraties in eval-report
- ✅ Reflection — wat werkte, wat niet, future work

Alle eisen worden gehaald op een non-Azure stack.

## Belangrijke architectuur-keuzes

### Beslissing 1 — chunking per pagina (PDF-aware)

**Probleem**: standaard PDF-loader concatte alle pagina's vóór chunking, waardoor chunks geen page-nummer wisten. Citation-knop voor diagrams werkte niet.

**Oplossing**: `load_pages(path)` retourneert lijst van `{page, text}`. Pipeline chunkt per pagina, tagt elke chunk met page-nummer. Cross-page chunks worden niet gecreëerd — kleine context-loss aan grenzen, maar gegarandeerde locator-integriteit.

**Trade-off**: vragen die expliciet over een page-grens-onderwerp gaan vinden mogelijk minder context. Voor coaching-content verwaarloosbaar — secties zijn meestal page-aligned.

### Beslissing 2 — single collection, metadata-filter

Vincent's blueprint stelde multi-collection voor (rules / coaching_theory / practice_plans / skills / tactics / age_groups). We hebben gekozen voor **single collection met rijke metadata** plus filter-mogelijkheid.

**Waarom**: bij 5.000 chunks geen scaling-noodzaak. Schema is wel multi-collection-ready (chunk metadata bevat `topic`, `authority`, `level` — query-filter werkt nu al).

**Wanneer splitsen**: bij Phase C4 (intent-classifier router) of corpus >50K chunks per type.

### Beslissing 3 — Haiku als default, Sonnet on-demand

Sonnet 4.6 produceert betere antwoorden, maar 10× duurder. Voor 95% van basketbal-vragen is Haiku 4.5 ruim voldoende — getest op de 20-vragen test-set. Sonnet bewaard voor:
- ADA eval-rondes (max-quality baseline)
- "Probeer met sterker model"-knop bij twijfelantwoorden (gepland)
- Premium ClubDuty-tier (gepland)

### Beslissing 4 — Authority metadata, geen query-routing yet

Elke chunk heeft `authority: official | semi-official | supplementary`. Citation-tier bepaalt visuele weight in de UI. **Nog NIET geïmplementeerd**: authority-weighted RRF (boost official bronnen). Dat is roadmap — eerst eval baseline meten, dan tunen.

### Beslissing 5 — In-process job-tracking, geen Redis

Admin uploads kunnen 30+ minuten duren (groot PDF + Contextual Retrieval). Gebruiker wacht niet op de HTTP-response — endpoint retourneert direct een `job_id` (HTTP 202), frontend pollt status elke 1.5s.

**In-memory store**: per worker process, met thread-safe lock. 1u TTL auto-prune. Acceptabel voor 2-worker setup. Voor multi-host scale: Redis (later).

### Beslissing 6 — Atomic ingest met rollback

Mislukte ingest (bv. AES-encrypted PDF zonder crypto-deps, niet-bereikbare URL) lieten orphaned manifest-entries achter. **Fix**: `_register_and_ingest` heeft try/except dat manifest-entry verwijdert + file unlinkt + chunks wist als ingest faalt. Gebruiker krijgt nette HTTP 500, geen vuile state.

## Observability (current + planned)

**Now**:
- API logs via uvicorn → docker-compose logs
- Per-job stage tracking → admin UI progress-bar
- Rate-limit headers (`X-RateLimit-Remaining-Day`, `Retry-After`)
- Healthcheck endpoint (`/health`)

**Planned (Phase B2)**:
- Structured query log (SQLite or JSONL) — wat vragen coaches echt
- Latency tracking per stage (retrieval, embed, LLM call)
- RAGAS-cijfers tracken over tijd voor regressie-detectie

## Security posture

| Concern | Mitigatie |
|---------|-----------|
| Admin endpoints | Bearer token via `ADMIN_TOKEN` env-var, constant-time compare |
| Public chat abuse | Per-IP rate-limit (20/dag, 10/uur), trust X-Forwarded-For |
| Cert acquisition | Caddy auto-Let's-Encrypt — geen manuele renewal |
| Secrets in repo | `.env` gitignored, `.env.example` in repo, ADMIN_TOKEN gegenereerd op server |
| Container isolation | Both containers bind to 127.0.0.1, alleen Caddy proxy't externally |
| Input validation | Pydantic schemas voor alle API-bodies; multipart-upload valideert file-extensions |

Geplande verbeteringen: OAuth voor remote MCP-flow, per-tenant API-keys, audit log voor admin-acties.

## Wat opzettelijk **niet** gebouwd is

- **Multi-tenancy** — schema-ready (`tenant_id` op elke chunk), maar geen tenant-isolation in admin-UI nog. Voor MVP overkill.
- **Smart chunkers** — drill-atomic, rule-article-atomic, chapter-aware. Schema-ready (`chunk_type` field), implementatie wacht op specifieke source-types die het rechtvaardigen.
- **GraphRAG** — sterke kandidaat voor multi-hop relationele basketbal-vragen, maar 4-6 dagen extra werk + $100-300 indexing kosten. Roadmap-fase D.
- **Multimodal embeddings** — CLIP voor diagram-embeddings. Fase D.
- **Reranker als 3e laag** — Cohere Rerank v3.5 of BGE-reranker-v2-m3. Pas zinvol als baseline precision tegenvalt.

Zie [`docs/eval-report.md`](eval-report.md) reflection-sectie voor uitgebreide bespreking.

## Externe afhankelijkheden

- **OpenRouter** voor LLM-routing — single point of failure. Mitigatie: model-swap is 1 env-var, alternatieve providers (direct Anthropic, OpenAI, lokaal Ollama) implementeerbaar zonder code-wijzigingen.
- **HuggingFace** voor bge-m3 model-download — eenmalig bij eerste container-start, gecached daarna.
- **Hetzner** voor hosting — een server. Backup-strategie nog te definiëren (chroma_data volume + sources.json + raw PDFs).
