#!/usr/bin/env python3
"""Iter #3 — Contextual Retrieval on/off A/B experiment.

Samples 3 representative Dutch/Flemish sources, reingests them with
contextual-retrieval enriched chunk prefixes, then compares retrieval-only
metrics against the baseline (current chunks without CR).

Why a sample and not the full corpus: a full-corpus CR reingest takes ~4 h on
the ARM host and costs ~$5-10 in LLM calls. The sample (243 chunks, 5-10 min,
<$0.50) is enough to show whether Anthropic's published 35-67% retrieval-error
reduction reproduces on this Dutch basketball corpus. If the sample is
positive, full rollout can be scheduled post-submission.

Run inside the api container:
    docker exec bbrain-api python /app/scripts/run_cr_experiment.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "api"))
sys.path.insert(0, "/app")

from app.eval.testset import TESTSET
from app.ingest.pipeline import ingest_corpus
from app.retrieval.bm25_index import BM25Index
from app.retrieval.chroma_store import ChromaStore
from app.retrieval.hybrid import hybrid_retrieve

# Sample sources — Dutch/Flemish to test CR on lower-resource-language content.
SAMPLE_IDS = [
    "nbb-handboek-trainers-en-coaches-2026-2027",       # 45 chunks, talent
    "nbb-5-5-basketball-spelregels-2025-2026",          # 71 chunks, rules
    "basketbal-vlaanderen-leerlijn-niveau-1-en-2",      # 127 chunks, philosophy
]


def _retrieval_eval(store: ChromaStore, bm25: BM25Index, top_k: int = 5) -> dict:
    """Retrieval-only eval, restricted to questions whose expected sources
    overlap with our sample (otherwise CR on those samples doesn't affect)."""
    sample_set = set(SAMPLE_IDS)
    recalls, precisions = [], []
    for item in TESTSET:
        expected = set(item["expected_source_ids"])
        if item["category"] == "out-of-scope" or not (expected & sample_set):
            continue
        chunks = hybrid_retrieve(item["question"], store, bm25, top_k=top_k)
        retrieved = {c.source_id for c in chunks}
        recall = len(expected & retrieved) / max(len(expected), 1)
        precision = (len(expected & retrieved) / max(len(retrieved), 1)) if retrieved else 0.0
        recalls.append(recall)
        precisions.append(precision)
    n = len(recalls)
    return {
        "n": n,
        "mean_recall_at_k": sum(recalls) / max(n, 1),
        "mean_precision": sum(precisions) / max(n, 1),
    }


def _reingest_sample_with_cr(store: ChromaStore, raw_dir: Path, manifest_path: Path) -> int:
    """Wipe the sample sources, then reingest them with CR enabled."""
    full_manifest = json.loads(manifest_path.read_text())
    sample = [e for e in full_manifest if e["id"] in SAMPLE_IDS]
    if len(sample) != len(SAMPLE_IDS):
        missing = set(SAMPLE_IDS) - {e["id"] for e in sample}
        raise RuntimeError(f"Missing sample sources in manifest: {missing}")

    for sid in SAMPLE_IDS:
        deleted = store.delete_by_source(sid)
        print(f"  wiped {sid}: -{deleted} chunks")

    tmp_manifest = raw_dir / ".cr-sample-manifest.json"
    tmp_manifest.write_text(json.dumps(sample))
    try:
        t0 = time.time()
        total = ingest_corpus(
            raw_dir, tmp_manifest, store,
            use_contextual_retrieval=True,
        )
        print(f"  reingested {total} chunks with CR in {time.time() - t0:.1f}s")
        return total
    finally:
        if tmp_manifest.exists():
            tmp_manifest.unlink()


def main() -> None:
    from app.config import settings

    chroma_dir = settings.chroma_persist_dir
    if not chroma_dir.startswith("/"):
        chroma_dir = str(Path("/app") / chroma_dir.lstrip("./"))
    raw_dir = Path("/app/data/raw")
    manifest_path = raw_dir / "sources.json"

    store = ChromaStore(persist_dir=chroma_dir)

    print("=" * 72)
    print("ITER #3 — CR on/off · BASELINE (current chunks, CR off)")
    print("=" * 72)
    bm25 = BM25Index(store.all_chunks())
    baseline = _retrieval_eval(store, bm25, top_k=5)
    print(f"  n={baseline['n']}  recall@5={baseline['mean_recall_at_k']:.3f}  "
          f"precision={baseline['mean_precision']:.3f}")

    print()
    print("=" * 72)
    print("REINGEST sample with CR=True")
    print("=" * 72)
    if not settings.openrouter_api_key:
        print("✗ OPENROUTER_API_KEY not set — cannot run CR enrichment. Abort.")
        return
    _reingest_sample_with_cr(store, raw_dir, manifest_path)

    print()
    print("=" * 72)
    print("ITER #3 — CR ON · sample reingested with contextual prefixes")
    print("=" * 72)
    bm25 = BM25Index(store.all_chunks())
    after = _retrieval_eval(store, bm25, top_k=5)
    print(f"  n={after['n']}  recall@5={after['mean_recall_at_k']:.3f}  "
          f"precision={after['mean_precision']:.3f}")

    # Append section to eval-report.md
    docs = Path("/app/docs/eval-report.md")
    if not docs.exists():
        docs = _HERE.parent / "docs" / "eval-report.md"
    lines = [
        "",
        "## Tuning iteratie #3 — Contextual Retrieval on/off",
        "",
        "Sample-experiment: 3 Nederlands-/Vlaamstalige bronnen (243 chunks totaal: "
        "`nbb-handboek-trainers-en-coaches-2026-2027`, "
        "`nbb-5-5-basketball-spelregels-2025-2026`, "
        "`basketbal-vlaanderen-leerlijn-niveau-1-en-2`) zijn herïngest met "
        "Anthropic's Contextual Retrieval — per-chunk prefix gegenereerd door "
        "Claude Haiku met prompt-caching op de document-prefix. Eval gefilterd "
        "op vragen waarvan minstens één verwachte bron in de sample zit.",
        "",
        "| config | recall@5 | precision | n |",
        "|--------|---------:|----------:|--:|",
        f"| CR off (baseline) | {baseline['mean_recall_at_k']:.3f} | "
        f"{baseline['mean_precision']:.3f} | {baseline['n']} |",
        f"| CR on (sample reingest) | {after['mean_recall_at_k']:.3f} | "
        f"{after['mean_precision']:.3f} | {after['n']} |",
        "",
        f"Δ recall@5: {after['mean_recall_at_k'] - baseline['mean_recall_at_k']:+.3f}, "
        f"Δ precision: {after['mean_precision'] - baseline['mean_precision']:+.3f}",
        "",
    ]
    body = "\n".join(lines)
    existing = docs.read_text() if docs.exists() else ""
    marker = "## Tuning iteratie #3"
    if marker in existing:
        existing = existing.split(marker)[0].rstrip() + "\n"
    docs.write_text(existing + body)
    print()
    print(body)
    print(f"Saved {docs}")


if __name__ == "__main__":
    main()
