<div align="center">

# 🏀 Basketball Brain

**Production-grade RAG for the Dutch basketball world**

NBB rules · FIBA rules · WABC coaching · USA Youth Development · talent-development research

[![Live](https://img.shields.io/badge/live-brain.clubduty.app-f5a524?style=flat-square)](https://brain.clubduty.app)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20Next.js%2016-2ecc71?style=flat-square)](#stack)
[![No Microsoft](https://img.shields.io/badge/no-Microsoft-red?style=flat-square)](#why-no-microsoft)

</div>

---

## TL;DR

A retrieval-augmented chatbot that gives **grounded answers** to anything a Dutch basketball coach, referee, or parent might ask. Every claim is traceable to the paragraph and page of a primary source. No hallucinations, no Microsoft stack, no vendor lock-in.

> **Question:** "What is a 5-out offence?"
> **Answer:** *"A **5-out** is an offensive set in which all five players position themselves outside the key, with no fixed post player…"*
> **Sources:** WABC Level 1 — section 2.1.5 (Motion offence — 5 out) · WABC Level 2 — section 2.1.4 (Post Up Cut "5 Out") · NBB 5x5 Rules · Wikipedia

Live demo: **<https://brain.clubduty.app>** · ADA RAG capstone · Foundation for the ClubDuty AI feature

---

## Contents

- [Why this project exists](#why-this-project-exists)
- [What it does](#what-it-does)
- [Stack](#stack)
- [Architecture](#architecture)
- [Corpus](#corpus)
- [Evaluation](#evaluation)
- [Run locally](#run-locally)
- [Production deployment](#production-deployment)
- [Roadmap](#roadmap)
- [Background](#background)

---

## Why this project exists

Three reasons at once:

1. **Capstone** for the ADA RAG course (Module 3 — *Build & Deploy a Production-Ready RAG Pipeline*).
2. **Feature foundation** for [ClubDuty](https://clubduty.nl) — a knowledge base for sports-club coaches.
3. **Practical execution** of *The Tireless Assistant* — the AI strategy I designed in Module 4 for BvH × ClubDuty.

The course brief specified Azure AI Search + Azure OpenAI. **I deliberately did not go that route.** See [Why no Microsoft](#why-no-microsoft).

## What it does

| Capability | Description |
|------------|-------------|
| **Hybrid retrieval** | BM25 (lexical, for exact terms like article numbers) + dense vectors (semantic, via bge-m3) + Reciprocal Rank Fusion |
| **Citation-first** | Every claim has a clickable source reference with title + section + page number |
| **Page thumbnails** | An eye-icon on every citation opens the rendered page image of the PDF — essential for diagrams (5-out plays, defensive setups, drills) |
| **Out-of-scope detection** | For questions outside the corpus the system explicitly says "I don't know" instead of hallucinating |
| **Multilingual** | Dutch question → Dutch answer, even when the source is English. English question → English answer. Jargon (`shot clock`, `pick and roll`) stays intact |
| **Admin UI** | Drag-drop PDF upload or URL fetch with live progress (no black-box waits); per-source metadata edit; reingest; page-thumbnail regenerate; delete |
| **Cost-aware** | Defaults to Claude Haiku 4.5 (~$0.002/query) via OpenRouter — model swap via env var. Per-IP rate limit (20/day, 10/hour) against scraper abuse |
| **Metrics dashboard** | `/admin/metrics` logs every query and eval run: volume, p50/p95 latency, mean similarity, OOS rate, top retrieved sources, improvement after tuning |

## Stack

<table>
<tr><th>Layer</th><th>Choice</th><th>Why</th></tr>
<tr>
  <td><b>Embeddings</b></td>
  <td><a href="https://huggingface.co/BAAI/bge-m3">BAAI/bge-m3</a> (1024-dim)</td>
  <td>Multilingual, strong on Dutch, MIT license, runs locally — no external call per query</td>
</tr>
<tr>
  <td><b>Vector store</b></td>
  <td>ChromaDB (PersistentClient)</td>
  <td>Self-hosted, HNSW cosine, simple Python API. Switch to Qdrant planned for multi-tenant scale</td>
</tr>
<tr>
  <td><b>Lexical lane</b></td>
  <td>rank_bm25</td>
  <td>In-process, rebuilt at startup. Fused via Reciprocal Rank Fusion (k=60)</td>
</tr>
<tr>
  <td><b>Indexing trick</b></td>
  <td><a href="https://www.anthropic.com/news/contextual-retrieval">Contextual Retrieval</a> (opt-in)</td>
  <td>Anthropic, Sept 2024 — chunk prefix via Claude Haiku with prompt caching. Reduces retrieval errors 35-67%. Off by default (free path), on for production</td>
</tr>
<tr>
  <td><b>LLM gateway</b></td>
  <td><a href="https://openrouter.ai">OpenRouter</a></td>
  <td>OpenAI-compatible API; switch between Claude/GPT/Gemini/local via env var. Defaults to <code>anthropic/claude-haiku-4-5</code></td>
</tr>
<tr>
  <td><b>API</b></td>
  <td>FastAPI + uv + uvicorn</td>
  <td>Async, Pydantic-validated, BackgroundTasks for long ingest jobs</td>
</tr>
<tr>
  <td><b>Frontend</b></td>
  <td>Next.js 16 (App Router) + Tailwind 4 + shadcn/ui</td>
  <td>Static prerender for / · /about · /admin. Tailwind 4 <code>@theme</code> for design tokens</td>
</tr>
<tr>
  <td><b>Eval</b></td>
  <td>RAGAS-style proxy + hand-curated test set</td>
  <td>20 hand-curated questions, 4 categories (lookup, philosophy, multi-doc, out-of-scope). Source-id-level recall as a pragmatic proxy for chunk-level RAGAS</td>
</tr>
<tr>
  <td><b>Metrics</b></td>
  <td>SQLite query log + eval-run history</td>
  <td>Per-query log of citations, similarity, latency, OOS flag. Eval runs persisted for "improvement after tuning" charts</td>
</tr>
<tr>
  <td><b>Deploy</b></td>
  <td>Hetzner ARM64 · docker-compose · host Caddy · Let's Encrypt</td>
  <td>Self-hosted, no Vercel lock-in. <code>brain.clubduty.app</code> integrates with the existing Caddy on the marketing server</td>
</tr>
</table>

### Why no Microsoft?

The course brief described Azure AI Search + Azure OpenAI + Azure Web App. Personal principled aversion to the Microsoft stack — and from a ClubDuty angle, a preference for open-source tooling wherever possible. ADA accepts non-Azure submissions; this repo demonstrates that the essence of the assignment (production-grade RAG, hybrid search, evaluation, live deployment) is achievable without Microsoft.

A side-by-side stack mapping lives in [`docs/architecture.md`](docs/architecture.md).

## Architecture

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
│  Next.js 16      │              │  ┌──────────────────────────┐   │
│  standalone      │              │  │ Hybrid retrieval         │   │
│  /, /about,      │              │  │  ChromaDB + BM25 + RRF   │   │
│  /admin          │              │  ├──────────────────────────┤   │
└──────────────────┘              │  │ Generation               │   │
                                  │  │  OpenRouter → Haiku/Sonnet │ │
                                  │  ├──────────────────────────┤   │
                                  │  │ Admin UI                 │   │
                                  │  │  CRUD + jobs + edit      │   │
                                  │  ├──────────────────────────┤   │
                                  │  │ Static /pages            │   │
                                  │  │  PDF page thumbnails     │   │
                                  │  └──────────────────────────┘   │
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

10 sources · ~4,500 chunks · 95% authority=`official` · multilingual (NL+EN).

| Source | Authority | Chunks | Type |
|--------|-----------|--------|------|
| FIBA Official Basketball Rules 2024 | official | 498 | rule |
| FIBA Official Interpretations 2024 (OBRI) | official | 681 | interpretation |
| FIBA WABC Mini Basketball Coaches Manual | official | 146 | philosophy (Mini) |
| FIBA WABC Coaching Manual Level 1 | official | 1,070 | philosophy (L1) |
| FIBA WABC Coaching Manual Level 2 | official | 916 | philosophy (L2) |
| USA Basketball Youth Development Guidebook | official | 910 | research / talent |
| NBB 5×5 Basketball Rules 2025-2026 | official | 71 | rule (NL) |
| Wooden — Pyramid of Success (Wikipedia) | supplementary | 158 | philosophy |
| Wikipedia — Basketball (NL) | supplementary | 83 | general |
| Wikipedia — Shot Clock (EN) | supplementary | 38 | rule |
| **Total** | | **~4,500** | |

Full metadata + sourcing discipline in [`docs/dataset.md`](docs/dataset.md).

## Evaluation

20 hand-curated questions, 4 categories:

| Category | n | Example |
|----------|---|---------|
| Lookup | 6 | "How long is the shot clock?" |
| Philosophy | 5 | "What are the core elements of Wooden's Pyramid of Success?" |
| Multi-document | 5 | "What guidance exists for 12-year-olds moving up to U14?" |
| Out-of-scope | 4 | "What is the capital of Australia?" → must answer "I don't know" |

Three tuning iterations (chunk size · hybrid weights · Contextual Retrieval on/off) with before/after numbers in [`docs/eval-report.md`](docs/eval-report.md).

## Run locally

Requirements: Python 3.12, Node 20+, [uv](https://github.com/astral-sh/uv), [bun](https://bun.sh) or npm, an [OpenRouter API key](https://openrouter.ai/keys).

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
# Fill in: OPENROUTER_API_KEY=sk-or-v1-...

# Optional: download corpus
bash ../scripts/download_sources.sh
python ../scripts/ingest_all.py

# Start API
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd ../web
npm install
cp .env.example .env.local
npm run dev   # http://localhost:3000
```

## Production deployment

Docker-compose on Hetzner ARM64 with a host Caddy reverse proxy. Full steps in [`infra/README.md`](infra/README.md). Short version:

```bash
ssh user@your-host
sudo apt install docker.io docker-cli docker-compose docker-buildx
sudo mkdir -p /opt/basketball-brain && sudo chown $USER /opt/basketball-brain
cd /opt/basketball-brain
git clone https://github.com/vincentblokker/basketball-brain .
cp api/.env.example api/.env  # fill in OPENROUTER_API_KEY + ADMIN_TOKEN
cd infra
docker-compose up -d --build
```

Caddyfile block for the reverse proxy + automatic HTTPS in `infra/README.md`.

## Roadmap

Four tracks · ADA deliverable / production pilot / ClubDuty feature / R&D — phased over 6-9 months. Short overview:

| Track | Goal | Highlights |
|-------|------|-----------|
| **A** ADA | Eval report + submit | 3 tuning iterations, reflection section |
| **B** Pilot quality | BvH coaches can actually use it | Local MCP server for Claude/Cursor; smart chunkers per source type; observability |
| **C** ClubDuty | Multi-tenant SaaS feature | Per-club content, auth layer, content CMS, remote MCP connector for Claude.ai/ChatGPT |
| **D** R&D | Differentiators | GraphRAG, multimodal embeddings (CLIP), voice, mobile PWA |

Full breakdown in my vincent-brain wiki under *[Basketball Brain — Roadmap]*.

## Background

| Document | What |
|----------|------|
| [`docs/architecture.md`](docs/architecture.md) | Stack rationale, design decisions, comparison with the Azure route |
| [`docs/dataset.md`](docs/dataset.md) | Corpus description, sourcing discipline, authority hierarchy |
| [`docs/eval-report.md`](docs/eval-report.md) | Test set, baseline, 3 tuning iterations, reflection |
| [`docs/submission.md`](docs/submission.md) | ADA submission checklist with links to every artefact |
| [`infra/README.md`](infra/README.md) | Deploy guide |

## Author

**Vincent Blokker** — Senior Product Strategist · UX Designer · AI

- Email: `vincentblokker@gmail.com`
- Project: [brain.clubduty.app](https://brain.clubduty.app)
- Part of: [ClubDuty](https://clubduty.nl)

## Acknowledgements

- **FIBA** for making the WABC manuals + Official Rules + Interpretations publicly available
- **USA Basketball** for the open-access Youth Development Guidebook
- **NBB** for the Dutch basketball context
- **Anthropic** for [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval), the Claude API, and the open MCP standard
- **BAAI** for [bge-m3](https://huggingface.co/BAAI/bge-m3) (multilingual embeddings)
- **Amsterdam Data Academy** for the RAG course that triggered this project
- **claude.ai/design** for the visual components — design tokens and micro-interactions

## License

MIT — see [LICENSE](./LICENSE).

> Free to reuse. Citations to this project (in academic work, talks, documentation) are appreciated but not required.
