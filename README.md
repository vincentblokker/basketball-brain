<div align="center">

# 🏀 Basketball Brain

**Production-grade RAG voor de Nederlandse basketbalwereld**

NBB-regels · FIBA-rules · WABC-coaching · USA Youth Development · onderzoek talentontwikkeling

[![Live](https://img.shields.io/badge/live-brain.clubduty.app-f5a524?style=flat-square)](https://brain.clubduty.app)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20Next.js%2016-2ecc71?style=flat-square)](#stack)
[![No Microsoft](https://img.shields.io/badge/no-Microsoft-red?style=flat-square)](#waarom-geen-microsoft)

</div>

---

## TL;DR

Een retrieval-augmented chatbot die **gegrond antwoord geeft** op alles wat een Nederlandse basketbalcoach, scheidsrechter of ouder zou kunnen vragen. Elke claim is traceerbaar naar de paragraaf en pagina van een primaire bron. Geen hallucinations, geen Microsoft-stack, geen vendor-lock-in.

> **Vraag:** "Wat is een 5-out aanval?"
> **Antwoord:** *"Een **5-out** is een offensieve opstelling waarbij alle vijf spelers zich aan de buitenkant van de sleutel positioneren, zonder een vaste postspeler…"*
> **Bronnen:** WABC Level 1 — sectie 2.1.5 (Motion offence — 5 out) · WABC Level 2 — sectie 2.1.4 (Post Up Cut "5 Out") · NBB 5x5 Spelregels · Wikipedia

Live demo: **<https://brain.clubduty.app>** · Eindopdracht ADA RAG · ClubDuty AI-feature-fundament

---

## Inhoud

- [Waarom dit project bestaat](#waarom-dit-project-bestaat)
- [Wat het doet](#wat-het-doet)
- [Stack](#stack)
- [Architectuur](#architectuur)
- [Corpus](#corpus)
- [Evaluatie](#evaluatie)
- [Lokaal draaien](#lokaal-draaien)
- [Productie-deployment](#productie-deployment)
- [Roadmap](#roadmap)
- [Achtergrond](#achtergrond)

---

## Waarom dit project bestaat

Drie redenen tegelijk:

1. **Eindopdracht** voor de ADA RAG-cursus (Module 3 — *Build & Deploy a Production-Ready RAG Pipeline*).
2. **Feature-fundament** voor [ClubDuty](https://clubduty.nl) — kennisbank voor sportclubcoaches.
3. **Praktische uitvoering** van *The Tireless Assistant* — de AI-strategie die ik in Module 4 ontwierp voor BvH × ClubDuty.

De cursus-opdracht schreef Azure AI Search + Azure OpenAI voor. **Ik heb dat bewust niet gedaan.** Zie [Waarom geen Microsoft](#waarom-geen-microsoft).

## Wat het doet

| Capability | Beschrijving |
|------------|--------------|
| **Hybrid retrieval** | BM25 (lexicaal, voor exacte termen als artikel-nummers) + dense vectors (semantisch, via bge-m3) + Reciprocal Rank Fusion |
| **Citaat-first** | Elke claim heeft klikbare bronvermelding met titel + sectie + pagina-nummer |
| **Page-thumbnails** | 👁-knop op elke citation opent de gerenderde pagina-foto van de PDF — onmisbaar voor diagrammen (5-out plays, defensive setups, drills) |
| **Out-of-scope detectie** | Bij vragen buiten het corpus zegt het systeem expliciet "Ik weet het niet" in plaats van hallucineren |
| **Meertalig** | NL-vraag → NL-antwoord, ook als de bron Engels is. EN-vraag → EN-antwoord. Vakjargon (`shot clock`, `pick and roll`) blijft natuurlijk intact |
| **Admin-UI** | Drag-drop PDF upload of URL-fetch met live progress (geen black-box wachten); per-source metadata-edit; reingest; page-thumbnail regenerate; verwijderen |
| **Cost-aware** | Default Claude Haiku 4.5 (~$0,002/vraag) via OpenRouter — model-swap via env-var. Per-IP rate-limit (20/dag, 10/uur) tegen scraper-abuse |

## Stack

<table>
<tr><th>Laag</th><th>Keuze</th><th>Waarom</th></tr>
<tr>
  <td><b>Embeddings</b></td>
  <td><a href="https://huggingface.co/BAAI/bge-m3">BAAI/bge-m3</a> (1024-dim)</td>
  <td>Multilingual, sterk op NL, MIT-licentie, lokaal draaibaar — geen externe call per query</td>
</tr>
<tr>
  <td><b>Vector store</b></td>
  <td>ChromaDB (PersistentClient)</td>
  <td>Self-host, hnsw cosine, eenvoudige Python-API. Switch naar Qdrant gepland bij multi-tenant scale</td>
</tr>
<tr>
  <td><b>Lexical lane</b></td>
  <td>rank_bm25</td>
  <td>In-process, rebuild-at-startup. Fuse via Reciprocal Rank Fusion (k=60)</td>
</tr>
<tr>
  <td><b>Indexing-trick</b></td>
  <td><a href="https://www.anthropic.com/news/contextual-retrieval">Contextual Retrieval</a> (opt-in)</td>
  <td>Anthropic sept 2024 — chunk-prefix via Claude Haiku met prompt caching. Reduceert retrieval-fouten met 35-67%. Default uit (gratis pad), aan voor productie</td>
</tr>
<tr>
  <td><b>LLM gateway</b></td>
  <td><a href="https://openrouter.ai">OpenRouter</a></td>
  <td>OpenAI-compatible API; switch tussen Claude/GPT/Gemini/lokaal via env-var. Default <code>anthropic/claude-haiku-4-5</code></td>
</tr>
<tr>
  <td><b>API</b></td>
  <td>FastAPI + uv + uvicorn</td>
  <td>Async, Pydantic-validated, BackgroundTasks voor lange ingest-jobs</td>
</tr>
<tr>
  <td><b>Frontend</b></td>
  <td>Next.js 16 (App Router) + Tailwind 4 + shadcn/ui</td>
  <td>Static-prerender voor / · /about · /admin. Tailwind 4 <code>@theme</code> voor design tokens</td>
</tr>
<tr>
  <td><b>Eval</b></td>
  <td>RAGAS-stijl proxy + handgecureerde test-set</td>
  <td>Hand-curated 20 vragen, 4 categorieën (lookup, philosophy, multi-doc, out-of-scope). Source-id-level recall als pragmatic proxy voor chunk-level RAGAS</td>
</tr>
<tr>
  <td><b>Deploy</b></td>
  <td>Hetzner ARM64 · docker-compose · host-Caddy · Let's Encrypt</td>
  <td>Self-hosted, no Vercel-lock-in. <code>brain.clubduty.app</code> integreert met bestaande Caddy op de marketing-server</td>
</tr>
</table>

### Waarom geen Microsoft?

De cursus-opdracht beschreef Azure AI Search + Azure OpenAI + Azure Web App. Persoonlijke principiële aversie tegen Microsoft-stack — én vanuit ClubDuty een wens voor open-source tooling waar mogelijk. ADA accepteert non-Azure submissions; deze repo bewijst dat de essentie van de opdracht (production-grade RAG, hybrid search, evaluation, live deployment) zonder Microsoft realiseerbaar is.

Vergelijkende stack-mapping in [`docs/architecture.md`](docs/architecture.md).

## Architectuur

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (mobile + desktop)              │
└─────────────────────────────────────────────────────────────────┘
                                  │ HTTPS
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              Caddy (host systemd, brain.clubduty.app)           │
│  /api/*  →  api:8000   (handle_path strips prefix)              │
│  /*      →  web:3000                                            │
└─────────────────────────────────────────────────────────────────┘
        │                                          │
        ▼                                          ▼
┌──────────────────┐              ┌─────────────────────────────────┐
│  bbrain-web      │              │  bbrain-api (FastAPI)           │
│  Next.js 16      │              │  ┌──────────────────────────┐  │
│  standalone      │              │  │ Hybrid retrieval         │  │
│  /, /about,      │              │  │  ChromaDB + BM25 + RRF   │  │
│  /admin          │              │  ├──────────────────────────┤  │
└──────────────────┘              │  │ Generation               │  │
                                  │  │  OpenRouter → Haiku/Sonnet  │
                                  │  ├──────────────────────────┤  │
                                  │  │ Admin UI                 │  │
                                  │  │  CRUD + jobs + edit      │  │
                                  │  ├──────────────────────────┤  │
                                  │  │ Static /pages            │  │
                                  │  │  PDF page-thumbnails     │  │
                                  │  └──────────────────────────┘  │
                                  └─────────────────────────────────┘
                                            │            │
                                            ▼            ▼
                                  ┌──────────────┐  ┌────────────┐
                                  │  ChromaDB    │  │ OpenRouter │
                                  │  /app/chroma │  │  (Claude)  │
                                  │  (volume)    │  └────────────┘
                                  └──────────────┘
                                            ▲
                                            │ ingest
                                  ┌──────────────────┐
                                  │  /app/data/raw   │
                                  │  PDFs + HTMLs    │
                                  │  + sources.json  │
                                  └──────────────────┘
```

## Corpus

10 bronnen · ~4.500 chunks · 95% authority=`official` · meertalig (NL+EN).

| Bron | Authority | Chunks | Type |
|------|-----------|--------|------|
| FIBA Official Basketball Rules 2024 | official | 498 | rule |
| FIBA Official Interpretations 2024 (OBRI) | official | 681 | interpretation |
| FIBA WABC Mini Basketball Coaches Manual | official | 146 | philosophy (Mini) |
| FIBA WABC Coaching Manual Level 1 | official | 1.070 | philosophy (L1) |
| FIBA WABC Coaching Manual Level 2 | official | 916 | philosophy (L2) |
| USA Basketball Youth Development Guidebook | official | 910 | research / talent |
| NBB 5×5 Basketball Spelregels 2025-2026 | official | 71 | rule (NL) |
| Wooden — Pyramid of Success (Wikipedia) | supplementary | 158 | philosophy |
| Wikipedia — Basketbal (NL) | supplementary | 83 | general |
| Wikipedia — Shot Clock (EN) | supplementary | 38 | rule |
| **Totaal** | | **~4.500** | |

Volledige metadata + sourcing-discipline in [`docs/dataset.md`](docs/dataset.md).

## Evaluatie

20 hand-curated vragen, 4 categorieën:

| Categorie | n | Voorbeeld |
|-----------|---|-----------|
| Lookup | 6 | "Hoe lang is de shot clock?" |
| Philosophy | 5 | "Wat zijn de kernelementen van Wooden's Pyramid of Success?" |
| Multi-document | 5 | "Welk advies bestaat over 12-jarigen die naar U14 doorschuiven?" |
| Out-of-scope | 4 | "Wat is de hoofdstad van Australië?" → moet "Ik weet het niet" |

Drie tuning-iteraties (chunk size · hybrid weights · Contextual Retrieval on/off) met before/after-cijfers in [`docs/eval-report.md`](docs/eval-report.md).

## Lokaal draaien

Vereisten: Python 3.12, Node 20+, [uv](https://github.com/astral-sh/uv), [bun](https://bun.sh) of npm, een [OpenRouter API-key](https://openrouter.ai/keys).

```bash
# Clone + setup
git clone https://github.com/vincentblokker/basketball-brain
cd basketball-brain

# Backend
cd api
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env
# Vul in: OPENROUTER_API_KEY=sk-or-v1-...

# Optioneel: download corpus
bash ../scripts/download_sources.sh
python ../scripts/ingest_all.py

# Start API
uvicorn app.main:app --reload --port 8000

# Frontend (apart terminal)
cd ../web
npm install
cp .env.example .env.local
npm run dev   # http://localhost:3000
```

## Productie-deployment

Docker-compose op Hetzner ARM64 met host-Caddy reverse-proxy. Volledige stappen in [`infra/README.md`](infra/README.md). Korte versie:

```bash
ssh user@your-host
sudo apt install docker.io docker-cli docker-compose docker-buildx
sudo mkdir -p /opt/basketball-brain && sudo chown $USER /opt/basketball-brain
cd /opt/basketball-brain
git clone https://github.com/vincentblokker/basketball-brain .
cp api/.env.example api/.env  # vul OPENROUTER_API_KEY + ADMIN_TOKEN in
cd infra
docker-compose up -d --build
```

Caddyfile-block voor reverse-proxy + automatische HTTPS in `infra/README.md`.

## Roadmap

Vier sporen · ADA-deliverable / production-pilot / ClubDuty-feature / R&D — gefaseerd over 6-9 maanden. Kort overzicht:

| Spoor | Doel | Highlights |
|-------|------|-----------|
| **A** ADA | Eval-rapport + submit | 3 tuning-iteraties, reflectie-sectie |
| **B** Pilot-quality | BvH-coaches kunnen ermee werken | MCP-server lokaal voor Claude/Cursor; smart chunkers per source-type; observability |
| **C** ClubDuty | Multi-tenant SaaS-feature | Per-club content, auth-laag, content-CMS, remote MCP-connector voor Claude.ai/ChatGPT |
| **D** R&D | Differentiators | GraphRAG, multimodal embeddings (CLIP), voice, mobile-PWA |

Volledige uitwerking in mijn vincent-brain wiki onder *[Basketball Brain — Roadmap]*.

## Achtergrond

| Document | Wat |
|----------|-----|
| [`docs/architecture.md`](docs/architecture.md) | Stack-rationale, design-besluiten, vergelijking met Azure-route |
| [`docs/dataset.md`](docs/dataset.md) | Corpus-beschrijving, sourcing-discipline, authority-hiërarchie |
| [`docs/eval-report.md`](docs/eval-report.md) | Test-set, baseline, 3 tuning-iteraties, reflectie |
| [`docs/submission.md`](docs/submission.md) | ADA inleveringschecklist met links naar alle artefacten |
| [`infra/README.md`](infra/README.md) | Deploy-handleiding |

## Author

**Vincent Blokker** — Senior Product Strategist · UX Designer · AI

- Email: `vincentblokker@gmail.com`
- Project: [brain.clubduty.app](https://brain.clubduty.app)
- Onderdeel van: [ClubDuty](https://clubduty.nl)

## Acknowledgements

- **FIBA** voor publieke beschikbaarheid van WABC-manuals + Official Rules + Interpretations
- **USA Basketball** voor de open-access Youth Development Guidebook
- **NBB** voor de Nederlandse basketbal-context
- **Anthropic** voor [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval), Claude API en de open MCP-standaard
- **BAAI** voor [bge-m3](https://huggingface.co/BAAI/bge-m3) (multilingual embeddings)
- **Amsterdam Data Academy** voor de RAG-cursus die dit project triggerde
- **claude.ai/design** voor de visuele componenten — design tokens en micro-interactions

## License

MIT — zie [LICENSE](./LICENSE).

> Vrij voor hergebruik. Citaten naar dit project (in academisch werk, in talks, in documentatie) worden gewaardeerd maar zijn niet vereist.
