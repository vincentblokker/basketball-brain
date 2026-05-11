

## Tuning iteratie #1 — top-k retrieval depth

Default RRF weights (1.0, 1.0). Retrieval-only metrics — geen LLM nodig voor recall@k of precision over source-ids. Out-of-scope vragen uitgesloten (alleen meaningful met LLM).

| top_k | recall@k | precision | n |
|------:|---------:|----------:|--:|
| 3 | 0.346 | 0.396 | 16 |
| 5 | 0.434 | 0.398 | 16 |
| 10 | 0.577 | 0.376 | 16 |

## Tuning iteratie #2 — hybrid weight balance

top_k=5 vast. Vergelijking pure-dense, pure-BM25 en gewogen mixes tegen de hybrid 1:1 baseline.

| config | recall@k | precision | n |
|--------|---------:|----------:|--:|
| hybrid 1:1 | 0.434 | 0.398 | 16 |
| dense-only | 0.405 | 0.443 | 16 |
| bm25-only | 0.281 | 0.203 | 16 |
| dense-heavy 2:1 | 0.419 | 0.448 | 16 |
| bm25-heavy 1:2 | 0.344 | 0.344 | 16 |

## Tuning iteratie #3 — Contextual Retrieval on/off

Sample-experiment: 3 Nederlands-/Vlaamstalige bronnen (243 chunks totaal: `nbb-handboek-trainers-en-coaches-2026-2027`, `nbb-5-5-basketball-spelregels-2025-2026`, `basketbal-vlaanderen-leerlijn-niveau-1-en-2`) zijn herïngest met Anthropic's Contextual Retrieval — per-chunk prefix gegenereerd door Claude Haiku met prompt-caching op de document-prefix. Eval gefilterd op vragen waarvan minstens één verwachte bron in de sample zit.

| config | recall@5 | precision | n |
|--------|---------:|----------:|--:|
| CR off (baseline) | 0.329 | 0.336 | 12 |
| CR on (sample reingest) | 0.304 | 0.329 | 12 |

Δ recall@5: -0.025, Δ precision: -0.007
