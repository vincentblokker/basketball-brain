"""Hand-curated test set for Basketball Brain MVP.

Categories: 6 lookup, 5 philosophy, 5 multi-doc, 4 out-of-scope.
Source-id-level recall is used as a pragmatic proxy for full RAGAS
chunk-level recall. Upgrade to chunk-level once chunk IDs are labelled
manually after iteration 1.
"""
from typing import TypedDict


class TestQuestion(TypedDict):
    question: str
    expected_source_ids: list[str]
    category: str


TESTSET: list[TestQuestion] = [
    # --- LOOKUP (6) ---
    {"question": "Hoe lang is de shot clock in basketbal?",
     "expected_source_ids": ["nbb-spelregels-2025-2026", "fiba-rules-2024", "wiki-shot-clock"],
     "category": "lookup"},
    {"question": "Wanneer wordt de 24-secondenklok gereset bij een offensive rebound?",
     "expected_source_ids": ["nbb-spelregels-2025-2026", "fiba-rules-2024"],
     "category": "lookup"},
    {"question": "Hoeveel persoonlijke fouten mag een speler maken voor uitschakeling?",
     "expected_source_ids": ["nbb-spelregels-2025-2026", "fiba-rules-2024"],
     "category": "lookup"},
    {"question": "Wat is de duur van een time-out volgens de NBB?",
     "expected_source_ids": ["nbb-spelregels-2025-2026"],
     "category": "lookup"},
    {"question": "Hoe groot is een basketbal speelveld volgens FIBA-regels?",
     "expected_source_ids": ["fiba-rules-2024"],
     "category": "lookup"},
    {"question": "Wat zegt de regel over goaltending?",
     "expected_source_ids": ["fiba-rules-2024", "nbb-spelregels-2025-2026"],
     "category": "lookup"},

    # --- PHILOSOPHY (5) ---
    {"question": "Wat zijn de kernelementen van Wooden's Pyramid of Success?",
     "expected_source_ids": ["wooden-pyramid"],
     "category": "philosophy"},
    {"question": "Welk advies geeft Wooden over hard werk?",
     "expected_source_ids": ["wooden-pyramid"],
     "category": "philosophy"},
    {"question": "Wat is de NBB-visie op talentontwikkeling bij jeugdspelers?",
     "expected_source_ids": ["nbb-talentontwikkeling"],
     "category": "philosophy"},
    {"question": "Welke principes hanteert de NBB voor jeugdtraining?",
     "expected_source_ids": ["nbb-talentontwikkeling"],
     "category": "philosophy"},
    {"question": "Wat zegt Wooden over de relatie tussen voorbereiding en succes?",
     "expected_source_ids": ["wooden-pyramid"],
     "category": "philosophy"},

    # --- MULTI-DOC (5) ---
    {"question": "Welk advies geeft 'te jong te snel' over 12-jarigen die naar U14 doorschuiven?",
     "expected_source_ids": ["te-jong-te-snel", "nbb-talentontwikkeling"],
     "category": "multi-doc"},
    {"question": "Hoe verschillen NBB- en FIBA-regels rondom de shot clock?",
     "expected_source_ids": ["nbb-spelregels-2025-2026", "fiba-rules-2024"],
     "category": "multi-doc"},
    {"question": "Wat zeggen onderzoek en NBB samen over leeftijdsgepaste training?",
     "expected_source_ids": ["te-jong-te-snel", "nbb-talentontwikkeling"],
     "category": "multi-doc"},
    {"question": "Welke risico's noemen meerdere bronnen bij vroeg specialiseren?",
     "expected_source_ids": ["te-jong-te-snel", "nbb-talentontwikkeling"],
     "category": "multi-doc"},
    {"question": "Hoe combineren coachfilosofie en jeugd-richtlijnen op het thema discipline?",
     "expected_source_ids": ["wooden-pyramid", "nbb-talentontwikkeling"],
     "category": "multi-doc"},

    # --- OUT-OF-SCOPE (4) ---
    {"question": "Wat is het beste pizza-recept?",
     "expected_source_ids": [],
     "category": "out-of-scope"},
    {"question": "Hoe werkt fotosynthese?",
     "expected_source_ids": [],
     "category": "out-of-scope"},
    {"question": "Wat is de hoofdstad van Australië?",
     "expected_source_ids": [],
     "category": "out-of-scope"},
    {"question": "Hoe werkt een quantum computer?",
     "expected_source_ids": [],
     "category": "out-of-scope"},
]
