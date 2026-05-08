from typing import Any

from fastapi import APIRouter, Depends

from app.deps import get_bm25, get_generator, get_store
from app.eval.runner import evaluate, results_to_dicts, summarize

router = APIRouter()

_StoreDep = Depends(get_store)
_BM25Dep = Depends(get_bm25)
_GenDep = Depends(get_generator)


@router.get("/eval/run")
def run_eval(
    store: Any = _StoreDep,
    bm25: Any = _BM25Dep,
    gen: Any = _GenDep,
) -> dict[str, Any]:
    results = evaluate(store, bm25, gen)
    return {
        "summary": summarize(results),
        "results": results_to_dicts(results),
    }
