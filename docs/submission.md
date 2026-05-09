# ADA-inlevering — Basketball Brain

> Module 3 — *Build & Deploy a Production-Ready RAG Pipeline*
>
> **Auteur**: Vincent Blokker
> **Datum**: [VUL IN bij submission]
> **Live demo**: <https://brain.clubduty.app>
> **GitHub**: <https://github.com/vincentblokker/basketball-brain>

## Volledige checklist

| Eis (uit Module 3 instructies) | Status | Artefact |
|--------------------------------|--------|----------|
| Live Web App URL (App Service) | ✅ | <https://brain.clubduty.app> |
| Stack configuration summary | ✅ | [README.md](../README.md) + [architecture.md](architecture.md) |
| Dataset description + source list | ✅ | [dataset.md](dataset.md) |
| Evaluation report (test set, results, before/after tuning) | [VUL IN] | [eval-report.md](eval-report.md) |
| Screenshots of Chat playground tests | [VUL IN] | `screenshots/` (zie hieronder) |
| (Optional) Metrics dashboard screenshot | — | Niet ingebouwd; reflectie over Grafana/Workbooks future-work |
| Short reflection (worked / didn't / would improve) | ✅ | [eval-report.md § Reflection](eval-report.md#reflection) |

## Hoe dit project afwijkt van de cursus-instructies

De cursus schreef **Azure AI Search + Azure OpenAI + Azure Web App** voor. Ik heb dat bewust niet gevolgd. Volledige stack-mapping en argumenten in [architecture.md § Vergelijking met de Azure-route](architecture.md#vergelijking-met-de-azure-route-uit-de-cursus). Korte samenvatting:

| Cursus (Azure) | Dit project | Why |
|----------------|-------------|-----|
| Azure AI Search | ChromaDB | Self-host, MIT, geen vendor-lock |
| Azure OpenAI | OpenRouter (Anthropic Claude) | Model-flexibiliteit + prompt-caching |
| Azure App Service | Hetzner ARM64 + docker-compose | Bestaande infra, $5/mo, full control |
| "Use your data" no-code | FastAPI + admin-UI | Volledige controle |

**Alle ADA-rubric-eisen worden gehaald** — production-style pipeline, hybrid search, evaluatie met before/after tuning, live deployment, reflectie. De rubric beoordeelt op het *concept* van een production-RAG, niet op merk-specifieke services.

## Bestand-overzicht voor de evaluator

```
basketball-brain/
├── README.md ......................... Project pitch + quickstart
├── docs/
│   ├── architecture.md ............... Stack-rationale, design-besluiten
│   ├── dataset.md .................... Corpus + sourcing-discipline
│   ├── eval-report.md ................ ⭐ Hoofdrapport voor ADA
│   ├── submission.md ................. Dit document — ADA inlevering checklist
│   └── screenshots/ .................. UI screenshots (zie hieronder)
├── api/
│   ├── app/ .......................... FastAPI backend
│   │   ├── routers/ .................. /query, /eval/run, /admin/*
│   │   ├── retrieval/ ................ ChromaDB, BM25, hybrid (RRF)
│   │   ├── ingest/ ................... PDF/HTML loader, chunker, page-images
│   │   ├── generation/ ............... LLM via OpenRouter
│   │   ├── eval/ ..................... Test-set + runner
│   │   └── admin/ .................... Auth, jobs, sources manager
│   ├── tests/ ........................ Pytest test suite
│   └── pyproject.toml
├── web/
│   └── app/, components/ ............. Next.js 16 frontend
├── infra/
│   ├── docker-compose.yml ............ Production stack
│   ├── caddy/Caddyfile ............... Host-Caddy reverse-proxy snippet
│   └── README.md ..................... Deploy-handleiding
├── scripts/
│   ├── download_sources.sh ........... Operator-only corpus fetch
│   └── ingest_all.py ................. One-shot ingest CLI
└── .github/workflows/
    └── ci.yml ........................ Lint + typecheck + build
```

## Live URLs voor de evaluator

| URL | Wat |
|-----|-----|
| <https://brain.clubduty.app/> | Chat-UI (homepage) — stel een vraag, krijg gegrond antwoord met citations |
| <https://brain.clubduty.app/about> | Over-pagina — stack, evaluatie-cijfers, bronnen |
| <https://brain.clubduty.app/admin> | Admin-UI (vereist token) — content management, edit metadata, regenerate pages |
| <https://brain.clubduty.app/api/health> | Health endpoint |
| <https://brain.clubduty.app/api/query> | RAG endpoint (POST `{question, top_k, tenant_id}`) |

## Aanbevolen evaluator-flow

1. **Open** <https://brain.clubduty.app/> in een browser
2. **Klik** op een suggestie-chip of typ een vraag, bijvoorbeeld:
   - "Hoe lang is de shot clock in basketbal?" (lookup)
   - "Wat zijn de kernelementen van Wooden's Pyramid of Success?" (philosophy)
   - "Welk advies geeft FIBA over coaching van 12-jarigen?" (multi-doc)
   - "Wat is de hoofdstad van Australië?" (out-of-scope — moet "Ik weet het niet" zeggen)
3. **Inspecteer** de citation-badges onder elk antwoord
4. **Klik** op de 👁-knop voor PDFs met paginalocator → opent gerenderde pagina als modal
5. **Open** [/about](https://brain.clubduty.app/about) voor stack-overview en evaluatie-cijfers
6. **Lees** [eval-report.md](eval-report.md) voor de drie tuning-iteraties + reflectie

## Test-vragen die de pipeline goed laten zien

| Vraag | Wat het demonstreert |
|-------|----------------------|
| "Hoe lang is de shot clock in basketbal?" | NL-vraag → NL-antwoord uit EN-bronnen, vergelijking FIBA/NBA/college |
| "Wanneer wordt de 24-secondenklok gereset bij offensive rebound?" | Specifieke regel-lookup, Hybrid search (BM25 vangt "24-secondenklok") |
| "Wat is een 5-out aanval?" | Concept uit FIBA WABC L1+L2, multi-doc citaten, page-thumbnail-knop voor diagram |
| "Welke principes hanteert de NBB voor jeugdtraining?" | NBB Talentontwikkeling — NL-bron |
| "Wat zegt Wooden over voorbereiding?" | Wooden Pyramid — supplementary bron, philosophy content_type |
| "Wat is fotosynthese?" | Out-of-scope — system zegt "Ik weet het niet op basis van de beschikbare bronnen" |

## Reflection — quick-link sections

- **Wat werkte**: stack-keuze, hybrid search, citation-first UI, TDD-ingest pipeline → [eval-report.md § Wat werkte](eval-report.md)
- **Wat niet werkte**: source-id-niveau recall als proxy, heuristic groundedness, gelimiteerde corpus-volume → [eval-report.md § Wat niet werkte / wat ik onderschat heb](eval-report.md)
- **Future work**: GraphRAG, alternatieve embeddings (voyage-3, bge-m3-large), reranker als 3e laag, chunk-level RAGAS metrics, multi-tenancy, LLM-judge groundedness → [eval-report.md § Wat ik in een vervolg zou onderzoeken](eval-report.md)

## Roadmap-positionering

Dit project is **MVP-fase 1** van een meerjaren-traject:

- **Phase A** (huidig) — ADA-deliverable
- **Phase B** (post-ADA, 1-2 mnd) — BvH-pilot productie-quality
- **Phase C** (3-6 mnd) — ClubDuty multi-tenant SaaS-feature
- **Phase D** (opportunistisch) — GraphRAG, multimodal embeddings, voice, mobile-PWA, MCP-connector voor Claude.ai/ChatGPT

De keuzes in deze MVP zijn **bewust ontworpen om Phase C-ready** te zijn — multi-tenant placeholder in schema, model-flexibiliteit via OpenRouter, schema-rijk met room voor query-routing.

## Contact

**Vincent Blokker**
- Email: vincentblokker@gmail.com
- Project: brain.clubduty.app
- Werkgever-context: ClubDuty (clubduty.nl)
