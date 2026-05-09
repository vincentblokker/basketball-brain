from typing import Any

from fastapi import APIRouter, Depends

from app.config import settings
from app.deps import get_bm25, get_generator, get_metrics, get_store
from app.eval.runner import evaluate, results_to_dicts, summarize
from app.metrics.store import MetricsStore

router = APIRouter()

_StoreDep = Depends(get_store)
_BM25Dep = Depends(get_bm25)
_GenDep = Depends(get_generator)
_MetricsDep = Depends(get_metrics)


@router.get("/eval/run")
def run_eval(
    store: Any = _StoreDep,
    bm25: Any = _BM25Dep,
    gen: Any = _GenDep,
    metrics: MetricsStore = _MetricsDep,
    notes: str | None = None,
) -> dict[str, Any]:
    results = evaluate(store, bm25, gen)
    summary = summarize(results)

    # Log this run for the dashboard's improvement-after-tuning chart.
    try:
        config = {
            "llm_model": settings.llm_model,
            "embedding_model": settings.embedding_model,
        }
        metrics.log_eval_run(
            config=config,
            n_questions=len(results),
            mean_recall=summary.get("mean_recall_at_k", 0.0),
            mean_precision=summary.get("mean_precision_source", 0.0),
            groundedness_rate=summary.get("groundedness_rate", 0.0),
            notes=notes,
        )
    except Exception:
        pass

    return {
        "summary": summary,
        "results": results_to_dicts(results),
    }
