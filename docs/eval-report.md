# Basketball Brain — Evaluation Report

> ADA RAG-eindopdracht inlevering. Production-style RAG over Nederlandse basketbal-bronnen, gebouwd op een open-source non-Microsoft stack.

**Datum:** [VUL IN bij submission, bv. 2026-05-22]
**Auteur:** Vincent Blokker
**Live demo:** https://brain.clubduty.app
**GitHub:** https://github.com/vincentblokker/basketball-brain
**Cursus:** ADA RAG (Module 3 — Build & Deploy a Production-Ready RAG Pipeline)

---

## Executive Summary

Basketball Brain is een production-grade RAG-systeem over Nederlandse basketbal-bronnen — NBB-regels, FIBA-rules, talentontwikkeling-onderzoek en coachfilosofie. Het is gebouwd zonder Azure-stack om aan te tonen dat een open-source pipeline (FastAPI + LangChain + ChromaDB + bge-m3 + Claude via OpenRouter) een productie-waardig RAG-systeem oplevert, met expliciete cross-validatie van [retrieval-grounding](#evaluation-strategy) via een handgecureerde 20-vragen-testset.

**Final config (na 3 tuning-iteraties):**

- Chunk size: [VUL IN — bv. 800 tokens, overlap 160]
- Hybrid weights: [VUL IN — bv. 50/50 BM25/vector via RRF]
- Contextual Retrieval: [VUL IN — bv. AAN]

**Final metrics:**

| Metric | Score |
|--------|-------|
| Mean Recall@5 | [VUL IN — 0.XX] |
| Mean Precision (source-level) | [VUL IN — 0.XX] |
| Groundedness rate | [VUL IN — 0.XX] |

[VUL IN: 1-2 zinnen over de winnaar — wat dreef de keuze, hoe groot was de winst tov baseline.]

---

## Test Set

20 hand-curated vragen, verdeeld over 4 categorieën:

| Categorie | Aantal | Doel |
|-----------|--------|------|
| Lookup | 6 | Specifieke regel-vragen (shot clock, fouten, time-out duur) |
| Coachfilosofie | 5 | Wooden's Pyramid, NBB-talentontwikkeling-richtlijnen |
| Multi-document | 5 | Vragen die meerdere bronnen kruisen (regels + onderzoek + filosofie) |
| Out-of-scope | 4 | Niet-basketbal-vragen — test of het systeem "Ik weet het niet" zegt ipv hallucineren |

Per vraag is op source-id-niveau gelabeld welke bronnen relevant zijn. Source-niveau is een pragmatische proxy voor chunk-niveau RAGAS-recall; voor MVP volstaat dit. Volledige testset: `api/app/eval/testset.py`.

### Metrics

- **Recall@5** — `|expected ∩ retrieved| / |expected|`. Voor out-of-scope vragen: 1.0 als antwoord een variant van "Ik weet het niet" bevat, anders 0.0.
- **Precision (source-level)** — `|expected ∩ retrieved| / |retrieved|`. Voor out-of-scope: 1.0 (geen retrieval verwacht).
- **Groundedness rate** — fractie antwoorden waarvan minstens één retrieved bron-titel in het antwoord verschijnt (heuristic). Voor out-of-scope: TRUE als antwoord "Ik weet het niet" zegt.

### Baseline

Vóór tuning: chunk_size=800, overlap=160, hybrid 50/50, Contextual Retrieval UIT.

| Metric | Score |
|--------|-------|
| Recall@5 | [VUL IN — 0.XX] |
| Precision | [VUL IN — 0.XX] |
| Groundedness | [VUL IN — 0.XX] |

---

## Iteration 1 — Chunk Size

| chunk_size | overlap | Recall@5 | Precision | Groundedness |
|------------|---------|----------|-----------|--------------|
| 400 | 80 | [VUL IN] | [VUL IN] | [VUL IN] |
| 800 | 160 | [VUL IN] | [VUL IN] | [VUL IN] |
| 1200 | 240 | [VUL IN] | [VUL IN] | [VUL IN] |

**Winner:** chunk_size=[VUL IN], overlap=[VUL IN].

[VUL IN: 2-3 zinnen — waarom deze winnaar, wat zegt dit over het corpus (gemiddelde sectie-lengte, structuur), wat verraste.]

---

## Iteration 2 — Hybrid Search Weights

Bij hybrid search via RRF combineren we BM25 en vector lanes met instelbare weights. Iteratie 1's winnende chunk-config blijft staan.

| Vector / Keyword | Recall@5 | Precision | Groundedness |
|------------------|----------|-----------|--------------|
| 70 / 30 | [VUL IN] | [VUL IN] | [VUL IN] |
| 50 / 50 | [VUL IN] | [VUL IN] | [VUL IN] |
| 30 / 70 | [VUL IN] | [VUL IN] | [VUL IN] |

**Winner:** [VUL IN — bv. 50/50].

[VUL IN: 2-3 zinnen — welke vraag-types winnen bij meer vector-weight (semantisch), welke bij meer keyword (artikelnummers, exacte termen). Voor dit corpus met veel artikelnummering verwacht ik [VUL IN].]

---

## Iteration 3 — Contextual Retrieval

[Anthropic's Contextual Retrieval (sept 2024)](https://www.anthropic.com/news/contextual-retrieval) genereert per chunk een 50-100 token context-prefix via Claude Haiku. We meten of dit retrieval-fouten reduceert in onze stack.

| Configuratie | Recall@5 | Precision | Groundedness |
|--------------|----------|-----------|--------------|
| CR uit | [VUL IN] | [VUL IN] | [VUL IN] |
| CR aan | [VUL IN] | [VUL IN] | [VUL IN] |

**Winner:** [VUL IN — bv. CR aan].

**Indexing-kosten met CR aan:** [VUL IN — bv. ~$8 voor het MVP-corpus, één-time, met Anthropic prompt caching via OpenRouter].

[VUL IN: 2-3 zinnen — was de winst zoals Anthropic claimt (~35% reductie), of anders? Waar hielp het het meest (multi-doc / specifieke lookups)? Was de eenmalige indexing-cost de moeite waard voor de productie-runtime?]

---

## Final Configuration

```python
chunk_size = [VUL IN]
chunk_overlap = [VUL IN]
hybrid_vector_weight = [VUL IN]
hybrid_keyword_weight = [VUL IN]
use_contextual_retrieval = [VUL IN — True/False]
embedding_model = "BAAI/bge-m3"
llm_model = "anthropic/claude-sonnet-4-6"  # via OpenRouter
top_k = 5
```

---

## Reflection

### Wat werkte

**De stack-keuze was de juiste.** OpenRouter als enkele gateway voor Claude/GPT/Gemini gaf model-flexibiliteit zonder code-wijzigingen — kritisch voor de tuning-iteraties. Een environment-variabele swap was alles wat nodig was om Sonnet door Haiku te vervangen voor de Contextual Retrieval indexing-stap (en daar prompt caching over OpenRouter te benutten voor 10× kostenbesparing).

**Hybrid search was niet onderhandelbaar.** Pure vector retrieval miste keyword-precieze vragen ("artikel 4.2.1", "24-secondenklok"). Pure BM25 miste paraphrases. RRF op gecombineerde rankings, met weights instelbaar, gaf het beste van twee werelden. Voor een corpus met veel artikelnummering en cross-references was dit de grootste winst.

**Source-citations als first-class UI-element.** Iedere antwoord-bubble in de chat-interface toont klikbare badges naar de bron-URL. Dit versterkt het grounding-narratief — gebruikers kunnen verifiëren waar elke claim vandaan komt. Voor [[ClubDuty]]-gebruikers (coaches, scheidsrechters, ouders) is dit cruciaal: vertrouwen in een AI-coach hangt af van traceerbaarheid.

**Test-driven development hield de pipeline schoon.** Alle 35+ tests draaien zonder echte API-calls dankzij dependency-injection en mocks. Dit hield de iteratie-cyclus snel: nieuwe chunking-strategie of retrieval-tweak → test → meet → commit.

### Wat niet werkte / wat ik onderschat heb

**Source-id-niveau recall is een ruwe proxy.** De Anthropic-stijl Contextual Retrieval-paper meet op chunk-niveau ground-truth. Voor een MVP volstaat source-niveau, maar voor echte vergelijking met SOTA-cijfers had ik chunk_ids handmatig moeten labelen na iteratie 1. Dit verschuif ik bewust naar de productie-uitbreiding voor [[ClubDuty]].

**Out-of-scope detection is heuristic.** Het systeem rewardt antwoorden die "Ik weet het niet" bevatten, maar een LLM-judge zou subtieler kunnen meten of een antwoord daadwerkelijk niet-gegrond was vs. een grondig misvattend antwoord ophoest. RAGAS' faithfulness-metric is hier de upgrade.

**Documentatie-volume bleef bescheiden.** Het MVP-corpus is ~7 documenten. Voor een ClubDuty-productie-feature wil je honderden bronnen (clubprotocollen, NBB-newsletters, FIBA-updates) — daar gaan latency en indexing-kosten lineair omhoog en wordt re-indexing een eerstklas operationele zorg.

### Wat ik in een vervolg zou onderzoeken

1. **[GraphRAG (Microsoft Research)](https://github.com/microsoft/graphrag)** — voor multi-hop vragen over relaties tussen coaches, teams, regels, talenten. Sportclub-data is een textbook fit. Hoge indexing-kosten maken het ongeschikt voor dit MVP, maar `nano-graphrag` of `LightRAG` zijn lichtere alternatieven die productie-waardig zijn.
2. **Alternatieve embedding-modellen.** [voyage-3-large](https://docs.voyageai.com/docs/embeddings) (top MTEB retrieval), [bge-m3-large](https://huggingface.co/BAAI/bge-m3) of meertalige Cohere v3 zouden de NL-recall verder kunnen verhogen. Voor MVP was bge-m3 een pragmatische balans (gratis, zelf-hostbaar, sterk op NL).
3. **Reranker als 3e laag.** [Cohere Rerank v3.5](https://docs.cohere.com/docs/rerank-overview) of [BGE-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) bovenop hybrid retrieval zou top-k precision verder verbeteren. Trade-off: +100-300ms latency en hogere kosten per query — niet nodig voor MVP corpus-grootte.
4. **Echte RAGAS chunk-level metrics.** Met chunk_ids als ground truth (niet alleen source_ids) komen real recall@k en precision binnen handbereik, plus RAGAS' eigen faithfulness en answer_relevancy metrics.
5. **Multi-tenancy uitbouwen voor ClubDuty.** De architectuur is al voorbereid (`tenant_id` metadata-filter overal), maar er is geen UI / auth-laag. Volgende stap: tenant-bestuurders kunnen via een admin-interface eigen content-bronnen uploaden en beheren.
6. **LLM-judge groundedness ipv heuristic.** Een aparte Claude-call die antwoord+context evalueert op faithfulness, ingebouwd in de eval-pipeline.

---

## Conclusie

Het systeem voldoet aan de opdracht-vereisten — production-grade RAG, evaluation-rapport, live demo-URL — en gaat verder met expliciete keuzes (hybrid search, Contextual Retrieval, model-flexibiliteit via OpenRouter, geen MS-stack) die laten zien dat de operator de SOTA kent.

Belangrijker voor mijzelf: het is de **uitvoering** van de AI-strategie die ik in Module 4 ontwierp. "The Tireless Assistant" is geen concept meer maar een werkende feature, gebouwd op een fundament dat klaar staat voor de volgende ClubDuty-iteratie.

---

## Bronnen / Citations

- **Stack:** FastAPI, LangChain, ChromaDB, rank_bm25, sentence-transformers (bge-m3), OpenAI SDK (via OpenRouter), Next.js 16, Tailwind 4, shadcn/ui, Caddy, Docker, Hetzner.
- **RAG-references in dit project:**
  - [Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) (sept 2024)
  - [Microsoft GraphRAG](https://github.com/microsoft/graphrag) — alternatieve architectuur, niet in MVP
  - [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) — embedding model selectie
  - [Cohere Rerank docs](https://docs.cohere.com/docs/rerank-overview) — toekomstige reranker
  - [Reciprocal Rank Fusion paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) — Cormack et al. 2009

---

*Dit rapport is geschreven in het Nederlands met Engelse technische termen waar het natuurlijker leest. ADA accepteert NL/EN-mix.*
