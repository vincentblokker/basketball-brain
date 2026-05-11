#!/usr/bin/env python3
"""Run tuning iterations and write before/after metrics to docs/eval-report.md.

Iterations:
  #1 — top-k retrieval depth: k ∈ {3, 5, 10}, default weights, default LLM
  #2 — hybrid weight balance: (vec,kw) ∈ {(1,1), (1,0), (0,1)}, k=5
  #3 — Contextual Retrieval on/off: requires full reingest, kicked off separately

Retrieval-only metrics (recall@k, precision over source-ids) — skip LLM for
speed + cost. Groundedness + OOS-IDK metrics require the LLM and are measured
separately in the regular /eval/run endpoint.

Run inside the api container:
    docker exec bbrain-api python /app/scripts/run_tuning.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

# Allow running both inside the container (/app/scripts/) and from repo root.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "api"))
sys.path.insert(0, "/app")

from app.eval.testset import TESTSET
from app.retrieval.bm25_index import BM25Index
from app.retrieval.chroma_store import ChromaStore
from app.retrieval.hybrid import hybrid_retrieve


def _retrieval_only_eval(
    store: ChromaStore,
    bm25: BM25Index,
    *,
    top_k: int,
    vector_weight: float,
    keyword_weight: float,
) -> dict[str, Any]:
    """Run eval without LLM. Measures recall@k + precision over source-ids."""
    n = len(TESTSET)
    recalls: list[float] = []
    precisions: list[float] = []
    by_cat: dict[str, list[float]] = {}
    t0 = time.time()
    for item in TESTSET:
        # Skip OOS for retrieval-quality metric — meaningless without LLM.
        if item["category"] == "out-of-scope":
            continue
        chunks = hybrid_retrieve(
            item["question"], store, bm25, top_k=top_k,
            vector_weight=vector_weight, keyword_weight=keyword_weight,
        )
        retrieved = {c.source_id for c in chunks}
        expected = set(item["expected_source_ids"])
        recall = len(expected & retrieved) / max(len(expected), 1)
        precision = (len(expected & retrieved) / max(len(retrieved), 1)) if retrieved else 0.0
        recalls.append(recall)
        precisions.append(precision)
        by_cat.setdefault(item["category"], []).append(recall)
    dt = time.time() - t0
    return {
        "n": len(recalls),
        "n_total": n,
        "mean_recall_at_k": sum(recalls) / max(len(recalls), 1),
        "mean_precision": sum(precisions) / max(len(precisions), 1),
        "by_category_recall": {c: sum(v) / len(v) for c, v in by_cat.items()},
        "latency_seconds": round(dt, 2),
    }


def main() -> None:
    from app.config import settings

    chroma_dir = settings.chroma_persist_dir
    if not chroma_dir.startswith("/"):
        chroma_dir = str(Path("/app") / chroma_dir.lstrip("./"))
    print(f"Chroma dir: {chroma_dir}")
    store = ChromaStore(persist_dir=chroma_dir)
    bm25 = BM25Index(store)
    bm25.rebuild()
    print(f"BM25 indexed {len(bm25.chunks)} chunks")

    print()
    print("=" * 72)
    print("TUNING ITERATION #1 — top-k retrieval depth")
    print("=" * 72)
    print(f"{'k':>4}  {'recall@k':>10}  {'precision':>10}  {'n':>3}  {'latency':>8}")
    results_topk: list[tuple[int, dict[str, Any]]] = []
    for k in (3, 5, 10):
        r = _retrieval_only_eval(store, bm25, top_k=k, vector_weight=1.0, keyword_weight=1.0)
        print(f"{k:>4}  {r['mean_recall_at_k']:>10.3f}  {r['mean_precision']:>10.3f}  {r['n']:>3}  {r['latency_seconds']:>7.1f}s")
        results_topk.append((k, r))

    print()
    print("=" * 72)
    print("TUNING ITERATION #2 — hybrid weight balance (top_k=5)")
    print("=" * 72)
    print(f"{'config':>20}  {'recall@k':>10}  {'precision':>10}  {'n':>3}  {'latency':>8}")
    configs = [
        ("hybrid 1:1", 1.0, 1.0),
        ("dense-only", 1.0, 0.0),
        ("bm25-only", 0.0, 1.0),
        ("dense-heavy 2:1", 2.0, 1.0),
        ("bm25-heavy 1:2", 1.0, 2.0),
    ]
    results_weights: list[tuple[str, dict[str, Any]]] = []
    for label, vw, kw in configs:
        r = _retrieval_only_eval(store, bm25, top_k=5, vector_weight=vw, keyword_weight=kw)
        print(f"{label:>20}  {r['mean_recall_at_k']:>10.3f}  {r['mean_precision']:>10.3f}  {r['n']:>3}  {r['latency_seconds']:>7.1f}s")
        results_weights.append((label, r))

    # ------ write Markdown summary ------
    out_path = _HERE.parent / "docs" / "eval-report.md"
    if not out_path.exists() and Path("/app/docs/eval-report.md").exists():
        out_path = Path("/app/docs/eval-report.md")

    lines: list[str] = []
    lines.append("\n## Tuning iteratie #1 — top-k retrieval depth\n")
    lines.append("Default RRF weights (1.0, 1.0). Retrieval-only metrics — geen LLM nodig "
                 "voor recall@k of precision over source-ids. Out-of-scope vragen "
                 "uitgesloten (alleen meaningful met LLM).\n")
    lines.append("| top_k | recall@k | precision | n |")
    lines.append("|------:|---------:|----------:|--:|")
    for k, r in results_topk:
        lines.append(f"| {k} | {r['mean_recall_at_k']:.3f} | {r['mean_precision']:.3f} | {r['n']} |")

    lines.append("\n## Tuning iteratie #2 — hybrid weight balance\n")
    lines.append("top_k=5 vast. Vergelijking pure-dense, pure-BM25 en gewogen mixes "
                 "tegen de hybrid 1:1 baseline.\n")
    lines.append("| config | recall@k | precision | n |")
    lines.append("|--------|---------:|----------:|--:|")
    for label, r in results_weights:
        lines.append(f"| {label} | {r['mean_recall_at_k']:.3f} | {r['mean_precision']:.3f} | {r['n']} |")

    body = "\n".join(lines) + "\n"
    print()
    print("=" * 72)
    print(f"Writing to: {out_path}")
    print("=" * 72)
    print(body)

    try:
        existing = out_path.read_text() if out_path.exists() else ""
    except Exception:
        existing = ""
    # Replace any prior tuning section so reruns don't duplicate.
    marker = "## Tuning iteratie #1"
    if marker in existing:
        existing = existing.split(marker)[0].rstrip() + "\n"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(existing + body)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
