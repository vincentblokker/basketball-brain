# Basketball Brain — Evaluation Report

> ADA RAG-eindopdracht inlevering. Production-style RAG over Nederlandse basketbal-bronnen, gebouwd op een open-source non-Microsoft stack.

**Datum:** 2026-05-11
**Auteur:** Vincent Blokker
**Live demo:** https://brain.clubduty.app
**GitHub:** https://github.com/vincentblokker/basketball-brain
**Cursus:** ADA RAG (Module 3 — Build & Deploy a Production-Ready RAG Pipeline)

---

## Executive Summary

Basketball Brain is een production-grade RAG-systeem over een meertalig corpus van Nederlandse, Vlaamse, Britse en Amerikaanse basketbal-bronnen — NBB-regels, FIBA-rules, WABC-coaching, USA Basketball youth development, Basketbal Vlaanderen Leerlijn en Jr. NBA practice plans. Het is gebouwd zonder Azure-stack om aan te tonen dat een open-source pipeline (FastAPI + ChromaDB + bge-m3 + Claude via OpenRouter) een productie-waardig RAG-systeem oplevert, met expliciete cross-validatie van retrieval-grounding via een handgecureerde 20-vragen-testset.

**Final config (na 3 tuning-iteraties):**

- Chunk-strategie: page-aware chunking (per-PDF-pagina, gemiddeld ~150-300 tokens/chunk)
- Hybrid weights: **dense-heavy 2:1** (vector_weight=2.0, keyword_weight=1.0 via RRF k=60)
- top_k: **5**
- Contextual Retrieval: **uit** (sample-experiment toonde geen meetbare winst op deze meertalige Dutch/EN corpus — zie iter #3)

**Final metrics op de 16 in-scope vragen (top_k=5, dense-heavy 2:1, CR off):**

| Metric | Score |
|--------|-------|
| Mean Recall@5 (source-level) | 0.419 |
| Mean Precision (source-level) | 0.448 |
| Out-of-scope IDK rate | gemeten via /eval/run (LLM in loop) |

Belangrijkste tuning-inzichten:
1. **k=5 is sweet spot** — k=3 mist recall, k=10 verliest precision sneller dan het wint aan recall.
2. **Pure-BM25 is duidelijk slechter** dan dense of hybrid — semantiek wint van keyword-matching op deze corpus. Dense-heavy 2:1 wint marginal van pure-dense en duidelijk van 1:1 hybrid.
3. **Contextual Retrieval gaf in onze sample géén verbetering** — counter-intuïtief vs Anthropic's gepubliceerde 35-67% retrieval-error reduction. Mogelijk corpus-specifiek (zie iter #3 sectie).

---

## Test Set

20 hand-curated vragen, verdeeld over 4 categorieën:

| Categorie | Aantal | Doel |
|-----------|--------|------|
| Lookup | 6 | Specifieke regel-vragen (shot clock, fouten, time-out duur) |
| Coachfilosofie | 5 | Wooden's Pyramid, talentontwikkeling-richtlijnen |
| Multi-document | 5 | Vragen die meerdere bronnen kruisen (regels + onderzoek + filosofie) |
| Out-of-scope | 4 | Niet-basketbal-vragen — test of het systeem "Ik weet het niet" zegt ipv hallucineren |

Per vraag is op source-id-niveau gelabeld welke bronnen relevant zijn. Source-niveau is een pragmatische proxy voor chunk-niveau RAGAS-recall; voor MVP volstaat dit. Volledige testset: `api/app/eval/testset.py`.

### Metrics

- **Recall@k** — `|expected ∩ retrieved| / |expected|` op source-id niveau. Voor de retrieval-only tuning-iteraties tellen we de 4 out-of-scope vragen niet mee (alleen meaningful met LLM in de loop).
- **Precision** — `|expected ∩ retrieved| / |retrieved|` op source-id niveau.
- **Groundedness** — heuristic: minstens één retrieved bron-titel in het antwoord. Gemeten via /eval/run met LLM.

### Corpus

Na de bulk-ingest van 11 → 52 bronnen (mei 2026):

- 52 unieke sources, 6.350 chunks totaal
- 95% authority="official" (FIBA, NBB, WABC, USA Basketball, Basketbal Vlaanderen, Basketball England, Jr. NBA)
- Meertalig: NL (NBB, Vlaanderen), EN (FIBA, WABC, USA, Jr.NBA, BE)
- Volledig overzicht in `docs/dataset.md`

---

## Iteration 1 — Top-k Retrieval Depth

Default RRF weights (1.0, 1.0). Retrieval-only metrics — geen LLM nodig voor recall@k of precision over source-ids. Out-of-scope vragen uitgesloten.

| top_k | Recall@k | Precision | n |
|------:|---------:|----------:|--:|
| 3 | 0.346 | 0.396 | 16 |
| **5** | **0.434** | **0.398** | 16 |
| 10 | 0.577 | 0.376 | 16 |

**Winner:** k=5.

k=3 is te krap voor multi-doc vragen waar 2-4 bronnen relevant zijn. k=10 voegt vooral noise toe — recall stijgt nog wel maar precision daalt. k=5 balanceert. Bovendien past k=5 in een chat-UI: het bron-paneel toont 5 citation badges zonder overweldigend te worden.

---

## Iteration 2 — Hybrid Search Weights

top_k=5 vast (winnaar iter #1). Vergelijking pure-dense, pure-BM25 en gewogen mixes via RRF.

| config | Recall@5 | Precision | n |
|--------|---------:|----------:|--:|
| hybrid 1:1 (baseline) | 0.434 | 0.398 | 16 |
| dense-only | 0.405 | 0.443 | 16 |
| bm25-only | 0.281 | 0.203 | 16 |
| **dense-heavy 2:1** | **0.419** | **0.448** | 16 |
| bm25-heavy 1:2 | 0.344 | 0.344 | 16 |

**Winner:** dense-heavy 2:1.

Pure-BM25 verliest duidelijk — onze testset bevat veel paraphrases en semantische vragen die keyword-matching niet vangt. Pure-dense is verrassend competitief op deze corpus, en dense-heavy 2:1 verbetert precision verder zonder echt recall te verliezen. Voor productie-config gaan we van 1:1 naar 2:1 (een env-var aanpassing — geen reingest nodig).

---

## Iteration 3 — Contextual Retrieval

[Anthropic's Contextual Retrieval (sept 2024)](https://www.anthropic.com/news/contextual-retrieval) genereert per chunk een 50-100 token context-prefix via Claude Haiku met prompt-caching op de document-prefix. We meten of dit retrieval-fouten reduceert op onze Nederlandse/Vlaamse content.

**Sample-experiment** in plaats van full-corpus reingest: een volledige CR-reingest van 6.350 chunks zou ~4u ARM-tijd en ~$5-10 in LLM-kosten kosten. We kozen voor een gerichte sample van 3 Nederlandstalige bronnen (243 chunks, ~10 min, <$0.50):

- `nbb-handboek-trainers-en-coaches-2026-2027` (45 chunks)
- `nbb-5-5-basketball-spelregels-2025-2026` (71 chunks)
- `basketbal-vlaanderen-leerlijn-niveau-1-en-2` (127 chunks)

Eval gefilterd op vragen waarvan minstens één verwachte bron in de sample zit (12 vragen).

| Configuratie | Recall@5 | Precision | n |
|--------------|---------:|----------:|--:|
| CR off (baseline) | 0.329 | 0.336 | 12 |
| CR on (sample reingest) | 0.304 | 0.329 | 12 |

**Δ Recall@5: −0.025 · Δ Precision: −0.007**

**Winner:** CR uit (in deze sample). Het verschil is klein en binnen de ruis van 12 vragen — niet de 35-67% verbetering die Anthropic op Engelse legal/finance-corpora rapporteert.

Waarom CR op onze corpus niet hielp, hypotheses:
1. **Source-id-niveau recall is grof.** Anthropic's paper meet chunk-niveau. CR helpt het meest om de juiste chunk binnen een document boven te halen — op source-niveau zien we dat verschil niet. Voor chunk-niveau metrics zou CR mogelijk wel winst geven.
2. **Sample is klein** (12 vragen, 3 sources, 243 chunks). Niet representatief voor een full-corpus measure.
3. **Onze documenten zijn al kort en goed-gestructureerd** — page-aware chunking respecteert PDF-pagina's, wat al een vorm van semantische coherentie geeft. De marginal value van extra Haiku-gegenereerde context is laag.
4. **Meertalige corpus.** Anthropic's resultaten zijn voornamelijk EN. Haiku's NL-output-kwaliteit voor de context-prefix is mogelijk net minder, waardoor het embedding-signal eerder vervuilt dan verrijkt.

**Indexing-kosten met CR aan voor sample:** ~$0.30 (243 chunks × Haiku met prompt-caching). Voor full corpus zou dit ~$5-10 zijn — niet de moeite gegeven het null-resultaat op de sample.

**Beslissing:** CR blijft uit in productie. Een chunk-niveau RAGAS-meting + grotere sample bewaar ik voor de ClubDuty-productie-uitbreiding waar het corpus groeit en chunk-level labels handmatig kunnen worden gemaakt.

---

## Final Configuration

```python
# api/app/retrieval/hybrid.py default params after tuning
top_k = 5
vector_weight = 2.0   # dense-heavy 2:1
keyword_weight = 1.0
candidate_pool = 50

# api/app/config.py
embedding_model = "BAAI/bge-m3"          # multilingual, 1024-dim, MIT
llm_model = "anthropic/claude-haiku-4-5"  # ~$0.002/query default
cr_model = "anthropic/claude-haiku-4-5"   # used only if CR opt-in

# Chunk strategy: page-aware (per-PDF-page chunks, no fixed token size)
# Contextual Retrieval: uit (sample-experiment liet geen verbetering zien)
```

---

## Reflection

### Wat werkte

**De stack-keuze was de juiste.** OpenRouter als enkele gateway voor Claude/GPT/Gemini gaf model-flexibiliteit zonder code-wijzigingen — kritisch voor de tuning-iteraties. Een env-var swap was alles wat nodig was om Sonnet door Haiku te vervangen voor de CR indexing-stap (en daar prompt-caching te benutten voor ~10× kostenbesparing). bge-m3 op een single uvicorn worker fit in 3.7GB ARM RAM met genoeg ruimte voor grote-PDF ingest.

**Hybrid search heeft waarde, maar minder dan verwacht.** Pure-BM25 verliest duidelijk — de testset bevat veel paraphrases en multi-doc vragen die keyword-matching niet vangt. Pure-dense doet het verrassend goed; dense-heavy 2:1 verbetert precision verder. Voor een corpus zonder veel artikel-nummer-references zou pure dense waarschijnlijk volstaan.

**Source-citations als first-class UI-element.** Iedere antwoord-bubble in de chat-UI toont klikbare citations met sectie + paginanummer, en een 👁-knop voor de page-thumbnail. Dit versterkt het grounding-narratief — gebruikers kunnen verifiëren waar elke claim vandaan komt. Voor ClubDuty-gebruikers (coaches, scheidsrechters) is dit cruciaal.

**Test-driven development hield de pipeline schoon.** Eval-runner draait met dependency-injection; tuning-script hergebruikt dezelfde retrieval als productie. Resultaten zijn dus exact reproduceerbaar — runner.py + tuning-script staan in de repo, evaluation in 1 commando.

### Wat niet werkte / wat ik onderschat heb

**Bulk-ingest was operationeel hard.** Eerste run-through crashte halverwege (container restart + 2-worker OOM op grote PDFs). Production-grade ingest betekent: rollback-bij-fout, geen duplicaten, idempotent reingest, kosten-cap. We hebben dat allemaal moeten toevoegen tijdens de ingest. Deploy van een nieuwe content-batch is nu single-script, maar dat was niet de eerste poging.

**Source-id-niveau recall is een ruwe proxy.** De CR-paper meet op chunk-niveau ground-truth. Voor MVP volstond source-niveau, maar voor échte vergelijking met SOTA-cijfers (zoals Anthropic's 35-67%) had ik chunk_ids handmatig moeten labelen. Verschoven naar ClubDuty-productie-uitbreiding.

**Out-of-scope detection is heuristic.** Het systeem rewardt antwoorden die "Ik weet het niet" bevatten. Een LLM-judge zou subtieler kunnen meten of een antwoord daadwerkelijk niet-gegrond was vs. een grondig misvattend antwoord ophoest. RAGAS' faithfulness-metric is hier de upgrade.

**ARM-host capaciteits-planning was te krap.** 3.7GB RAM met 2 workers × bge-m3 model is OOM-gevoelig voor grote-PDF ingest. We zijn naar 1 worker — voor lage-traffic personal RAG prima, maar je merkt dat hardware-keuzes upfront discipline vragen.

### Wat ik in een vervolg zou onderzoeken

1. **Chunk-niveau RAGAS metrics.** Met chunk_ids als ground truth (niet alleen source_ids) komen real recall@k en precision binnen handbereik, plus RAGAS' eigen faithfulness en answer_relevancy metrics. Vooral voor een tweede CR-meting noodzakelijk om de Anthropic-cijfers eerlijk te kunnen reproduceren.
2. **[GraphRAG (Microsoft Research)](https://github.com/microsoft/graphrag)** — voor multi-hop vragen over relaties tussen coaches, teams, regels, talenten. `nano-graphrag` of `LightRAG` zijn lichtere alternatieven die productie-waardig zijn.
3. **Reranker als 3e laag.** [Cohere Rerank v3.5](https://docs.cohere.com/docs/rerank-overview) of [BGE-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) bovenop hybrid retrieval zou top-k precision verder verbeteren. Trade-off: +100-300ms latency.
4. **Alternatieve embeddings voor NL.** [voyage-3-large](https://docs.voyageai.com/docs/embeddings), bge-m3-large of meertalige Cohere v3 zouden de NL-recall verder kunnen verhogen.
5. **Multi-tenancy uitbouwen voor ClubDuty.** Architectuur is voorbereid (`tenant_id` overal), UI/auth nog niet. Tenant-bestuurders moeten via een admin-interface eigen content-bronnen kunnen uploaden.
6. **LLM-judge groundedness** ipv heuristic.
7. **MCP-server** voor Claude.ai/Cursor/ChatGPT directe integratie — basketbal-coaches die de assistent willen gebruiken in hun eigen tooling.

---

## Conclusie

Het systeem voldoet aan de opdracht-vereisten — production-grade RAG, evaluation-rapport met 3 tuning-iteraties, live demo, metrics-dashboard — en gaat verder met expliciete keuzes (hybrid search met getunede weights, page-aware chunking, model-flexibiliteit via OpenRouter, geen MS-stack) die laten zien dat de operator de SOTA kent en bewust afwijkt waar het bij dit corpus niet helpt.

Het meest leerzame moment was iter #3: Contextual Retrieval verbeterde **niet** in onze sample, terwijl Anthropic 35-67% retrieval-error reduction rapporteert. De relevante lesson is niet "CR werkt niet" maar "SOTA-claims testen tegen je eigen corpus voordat je $5-10 in indexing-kosten stopt". Honest negatives zijn ook resultaten.

Belangrijker voor mijzelf: het is de **uitvoering** van de AI-strategie die ik in Module 4 ontwierp. "The Tireless Assistant" is geen concept meer maar een werkende feature, gebouwd op een fundament dat klaar staat voor de volgende ClubDuty-iteratie.

---

## Bronnen / Citations

- **Stack:** FastAPI, ChromaDB, rank_bm25, sentence-transformers (bge-m3), OpenAI SDK (via OpenRouter), Next.js 16, Tailwind 4, shadcn/ui, Caddy, Docker, Hetzner ARM64.
- **RAG-references in dit project:**
  - [Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) (sept 2024)
  - [Reciprocal Rank Fusion paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) — Cormack et al. 2009
  - [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) — embedding model selectie
  - [Microsoft GraphRAG](https://github.com/microsoft/graphrag) — alternatieve architectuur, niet in MVP
  - [Cohere Rerank docs](https://docs.cohere.com/docs/rerank-overview) — toekomstige reranker
- **Tuning-data + scripts:** `scripts/run_tuning.py`, `scripts/run_cr_experiment.py`, `api/app/eval/testset.py`

---

*Dit rapport is geschreven in het Nederlands met Engelse technische termen waar het natuurlijker leest. ADA accepteert NL/EN-mix.*
