# Dataset

Het corpus van Basketball Brain: 10 publieke bronnen, ~4.500 chunks, gecentreerd op de Nederlandse basketbalwereld met internationale officiële bronnen als ankerpunt.

## Sourcing-filosofie

**Strict primary-sources-only.** LLMs zijn gebruikt om bronnen te **vinden** (research/triangulation across Claude, GPT, Gemini, Grok, Perplexity), niet om inhoud te **genereren**. Geen LLM-output gaat de knowledge base in. Reden: RAG over LLM-output route hallucinations door een extra laag heen — antwoorden klinken autoritatiever zonder dat de feitelijke betrouwbaarheid stijgt.

Schema-veld `source_type` onderscheidt:
- `primary` — de daadwerkelijke bron (alle huidige content)
- `synthesized` — gereserveerd voor toekomstige LLM-samenvattingen, expliciet gelabeld zodat retrieval-filters ze kunnen uitsluiten

## Authority-hiërarchie

Elke bron heeft een `authority`-tag in metadata:

| Niveau | Betekenis | Bronnen in corpus |
|--------|-----------|-------------------|
| `official` | Normatief document van de bond/instantie zelf | FIBA Rules, FIBA OBRI, FIBA WABC manuals (Mini/L1/L2), USA Basketball Youth Dev, NBB Spelregels |
| `semi-official` | Door bonden erkend maar niet bindend | (geen in huidige corpus) |
| `supplementary` | Algemene of educatieve referentie | Wooden Pyramid (Wikipedia), NL Wikipedia basketbal, EN Wikipedia shot clock |

In retrieval-tijd wordt authority **nog niet** gewogen in de RRF-score (roadmap-feature). Frontend toont authority subtiel via citation-styling.

## Volledige source-list

### 1. FIBA Official Basketball Rules 2024

| Veld | Waarde |
|------|--------|
| ID | `fiba-official-basketball-rules-2024` |
| Authority | `official` |
| Ruleset | `FIBA` |
| Type | `rule` |
| Taal | `en` |
| Pagina's | 105 |
| Chunks | 498 |
| Bron | <https://refereeing.fiba.basketball/en/rules> |
| Geldig | sinds 1 oktober 2024 |

Officiële regels van FIBA. De normatieve bron voor alle internationale en NBB-gereguleerde basketbal vanaf de seizoen 2024-2025.

### 2. FIBA Official Interpretations 2024 (OBRI)

| Veld | Waarde |
|------|--------|
| ID | `fiba-official-interpretations-2024-obri` |
| Authority | `official` |
| Ruleset | `FIBA` |
| Type | `general` (interpretation) |
| Topic | `interpretation` |
| Taal | `en` |
| Pagina's | 142 |
| Chunks | 681 |
| Bron | <https://refereeing.fiba.basketball/en/rules> |

Interpretatie-document bij de Rules. Bevat case-uitleg en edge-cases die scheidsrechters nodig hebben. Categorisch niet de regels zelf maar de toepassing daarvan — daarom `content_type=general` met `topic=interpretation` in plaats van `rule`.

### 3. FIBA WABC Mini Basketball Coaches Manual

| Veld | Waarde |
|------|--------|
| ID | `fiba-wabc-mini-basketball-coaches-manual` |
| Authority | `official` |
| Level | `Mini` |
| Type | `philosophy` |
| Topic | `coaching-philosophy` |
| Age | `U10` |
| Taal | `en` |
| Pagina's | 52 |
| Chunks | 146 |
| Bron | <https://about.fiba.basketball/en/wabc-documents> |

Coaching voor 8-10 jaar — game-based teaching, fundamentals zonder saaie rijtjesdrills.

### 4. FIBA WABC Coaching Course Manual — Level 1

| Veld | Waarde |
|------|--------|
| ID | `fiba-wabc-coaching-course-manual-level-1` |
| Authority | `official` |
| Level | `L1` |
| Type | `philosophy` |
| Topic | `coaching-philosophy` |
| Age | `all` |
| Taal | `en` |
| Pagina's | ~250+ |
| Chunks | 1.070 |
| Bron | <https://about.fiba.basketball/en/wabc-documents> |

Basis voor elke coach. Rol van de coach, leren, skills, training, communicatie, motion-offence (incl. 5-out), defensieve fundamentals.

### 5. FIBA WABC Coaching Course Manual — Level 2

| Veld | Waarde |
|------|--------|
| ID | `fiba-wabc-coaching-course-manual-level-2` |
| Authority | `official` |
| Level | `L2` |
| Type | `philosophy` |
| Topic | `coaching-philosophy` |
| Age | `all` |
| Taal | `en` |
| Pagina's | ~200+ |
| Chunks | 916 |
| Bron | <https://about.fiba.basketball/en/wabc-documents> |

Team-ontwikkeling, leadership, geavanceerde tactiek, post-up cuts (waaronder "5 Out"), team-cultuur. Voor coaches die voorbij fundamentals willen.

### 6. USA Basketball Youth Development Guidebook

| Veld | Waarde |
|------|--------|
| ID | `usa-basketball-youth-development-guidebook` |
| Authority | `official` |
| Type | `research` |
| Topic | `talent-development` |
| Region | `USA` |
| Age | `U10,U12,U14,U16,U18` |
| Taal | `en` |
| Pagina's | ~100+ |
| Chunks | 910 |
| Bron | <https://www.usab.com/play/the-usa-basketball-coaching-guide-for-all-levels/usa-basketball-youth-development-guidebook> |

Player development curriculum. Beantwoordt: wat hoort een 14-jarige te kunnen, wanneer start je met krachttraining, hoe bouw je skills progressief op, leeftijdsgericht trainen, lange-termijn talentontwikkeling.

### 7. NBB 5×5 Basketball Spelregels 2025-2026

| Veld | Waarde |
|------|--------|
| ID | `nbb-5-5-basketball-spelregels-2025-2026` |
| Authority | `official` |
| Ruleset | `FIBA` (door NBB toegepast) |
| Type | `rule` |
| Region | `NL` |
| Taal | `nl` |
| Chunks | 71 |
| Bron | <https://basketball.nl/kennishub/basketball/5-5-basketball/> |

Nederlandse versie/samenvatting van de 5x5-spelregels door de Nederlandse Basketball Bond. Belangrijk voor NL-context en NL-jargon.

### 8. Wooden — Pyramid of Success (Wikipedia)

| Veld | Waarde |
|------|--------|
| ID | `wooden-pyramid` |
| Authority | `supplementary` |
| Type | `philosophy` |
| Taal | `en` |
| Chunks | 158 |
| Bron | <https://en.wikipedia.org/wiki/Pyramid_of_Success> |

15 elementen van John Wooden's coaching-filosofie. Tijdloze coaching-wijsheid, breed bekend in basketbal-coaching-cultuur.

### 9. Wikipedia — Basketbal (NL)

| Veld | Waarde |
|------|--------|
| ID | `wiki-nl-basketbal` |
| Authority | `supplementary` |
| Type | `general` |
| Region | `NL` |
| Taal | `nl` |
| Chunks | 83 |
| Bron | <https://nl.wikipedia.org/wiki/Basketbal> |

Algemene NL-context, definities, geschiedenis. Vangnet voor "wat is X?"-vragen wanneer specifieke bronnen geen antwoord geven.

### 10. Wikipedia — Shot Clock (EN)

| Veld | Waarde |
|------|--------|
| ID | `wiki-shot-clock` |
| Authority | `supplementary` |
| Type | `rule` |
| Taal | `en` |
| Chunks | 38 |
| Bron | <https://en.wikipedia.org/wiki/Shot_clock> |

Algemene context bij shot-clock-vragen, biedt vergelijking tussen FIBA / NBA / NCAA.

## Metadata-schema per chunk

Elke chunk in ChromaDB heeft naast text en embedding deze metadata-velden:

```python
{
    # Identiteit
    "source_id": "fiba-wabc-coaching-course-manual-level-1",
    "chunk_id": "fiba-wabc-...-42-a3f8c1d2",
    "chunk_index": 42,

    # Multi-tenancy (placeholder, default "public")
    "tenant_id": "public",

    # Authority + content-type (taxonomie)
    "source_type": "primary",        # primary | synthesized
    "authority": "official",          # official | semi-official | supplementary
    "content_type": "philosophy",     # rule | philosophy | research | general
    "topic": "coaching-philosophy",   # vrije tag, vaak shooting/spacing/talent-dev/...
    "level": "L1",                    # n/a | Mini | L1/2/3 | Rookie/Starter/All-Star/MVP
    "ruleset": "",                    # FIBA | NBA | NCAA | leeg
    "region": "international",        # international | NL | USA | EU | other
    "audience": "coach",              # comma-separated: coach,referee,parent,player,all
    "age_category": "all",            # all | U10/12/14/16/18 | senior

    # Locator
    "title": "FIBA WABC Coaching Course Manual — Level 1",
    "url": "https://assets.fiba.basketball/...",
    "page": 47,                       # 1-indexed PDF page; -1 voor non-PDF
    "section": "",                    # vrij veld, gepland voor heading-aware chunker

    # Inhoud
    "language": "en",
    "chunk_type": "prose",            # prose | rule_article | drill | chapter
    "contextual_prefix": "",          # Anthropic CR prefix wanneer enabled
}
```

## Sourcing-discipline in de praktijk

Toen we de 8 priority sources moesten vinden, hebben we niet één LLM gevraagd "wat zijn de beste FIBA-coaching-PDFs?" en blind gevolgd. We hebben:

1. Voor elke gewenste bron de **officiële landing-pagina** opgespoord (about.fiba.basketball, refereeing.fiba.basketball, usab.com)
2. De **directe PDF-URL** gehaald (HTTP 200 + `application/pdf` MIME geverifieerd)
3. Via **WebFetch / curl** met juiste User-Agent gedownload
4. **PDF-magic-bytes** (`%PDF`) gecontroleerd vóór ingest

Voor sources die login vereisten of niet publiekelijk te krijgen waren (sommige Jr. NBA practice plans hebben dat soms): expliciet gemarkeerd als `LOGIN_REQUIRED` en handmatig door Vincent gedownload.

## Wat **niet** in het corpus zit (en waarom)

| Bron | Reden |
|------|-------|
| Jr. NBA Practice Plans (All-Star + MVP, 26 PDFs) | Bewust uitgesteld — voor ADA-eval-scope te veel ruis en lange ingest. Roadmap-fase B3 |
| Breakthrough Basketball, YMCA-manuals | Lager-autoriteit, commercieel/blogachtig. Niet nodig voor MVP-scope, kan als `supplementary` later |
| Boeken zoals "Coaching Basketball Successfully" | Copyright. Wordt niet ingezet |
| Internationale rule-sets (NBA, NCAA, Euroleague) | Buiten scope (Nederlandse focus). Mogelijk later voor multi-rules-tier feature |
| BvH-clubprotocollen | Privé-data, GDPR. Past in toekomstige multi-tenant ClubDuty-feature met per-club content |
| Talent-onderzoek "Te jong, te snel" | Vincent's eigen kopie — handmatig in te uploaden via admin-UI bij gelegenheid |

## Volume-projectie

Bij groei naar ClubDuty multi-tenant:

- **MVP (nu)**: 10 bronnen, 4.500 chunks. ChromaDB: ~50 MB.
- **BvH-pilot (Phase B)**: +20 NL-specifieke bronnen, ~7K chunks
- **ClubDuty-pilot (Phase C)**: 5-10 clubs, elk 30-50 club-specifieke bronnen, 50-100K chunks totaal
- **Switch naar Qdrant**: zodra >50K chunks per tenant of >100K totaal

ChromaDB schaalt op embeddings-volume: 4.500 chunks gebruikt ~50 MB; 50K chunks zou ~500 MB zijn. Hetzner CAX21 disk is 38 GB — meer dan genoeg headroom voor groei tot Phase C.

## Re-ingest discipline

Wanneer chunking-strategie of metadata-schema wijzigt:

1. **Per-source reingest** via admin-UI 🔄-knop — wist chunks van die source uit Chroma, leest de file opnieuw, chunkt opnieuw, embed opnieuw
2. **Volledig wipe** via `docker-compose down && docker volume rm infra_chroma_data && docker-compose up && docker-compose exec api python /app/scripts/ingest_all.py`
3. **Append-only** (default) — `python scripts/ingest_all.py` voegt toe aan bestaande, dupliceert chunks bij re-run

ChromaDB chunk-IDs hebben een uuid-suffix; re-run zonder eerst delete maakt dus duplicate chunks. Daarom: wipe-eerst voor schone state.
