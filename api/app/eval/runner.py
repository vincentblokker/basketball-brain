from dataclasses import asdict, dataclass
from typing import Any

from app.eval.testset import TESTSET
from app.retrieval.bm25_index import BM25Index
from app.retrieval.chroma_store import ChromaStore
from app.retrieval.hybrid import hybrid_retrieve


@dataclass
class EvalResult:
    question: str
    category: str
    expected_source_ids: list[str]
    retrieved_source_ids: list[str]
    answer: str
    # |expected ∩ retrieved| / |expected|; 1.0 if expected empty AND answer is IDK
    recall_at_k: float
    # |expected ∩ retrieved| / |retrieved|
    precision_source: float
    # heuristic: answer mentions at least one retrieved source title
    grounded: bool


def _heuristic_grounded(answer: str, retrieved_titles: list[str]) -> bool:
    return any(t.lower()[:20] in answer.lower() for t in retrieved_titles if t)


def _is_idk(answer: str) -> bool:
    lo = answer.lower()
    return "weet het niet" in lo or "i don't know" in lo or "ik weet" in lo


def evaluate(
    store: ChromaStore,
    bm25: BM25Index,
    gen: Any,
    top_k: int = 5,
) -> list[EvalResult]:
    results: list[EvalResult] = []
    for item in TESTSET:
        chunks = hybrid_retrieve(item["question"], store, bm25, top_k=top_k)
        retrieved_source_ids = list({c.source_id for c in chunks})
        expected = set(item["expected_source_ids"])
        retrieved = set(retrieved_source_ids)
        answer = gen.answer(item["question"], chunks)

        if item["category"] == "out-of-scope":
            recall = 1.0 if _is_idk(answer) else 0.0
            precision = 1.0
            grounded = recall == 1.0
        else:
            recall = len(expected & retrieved) / max(len(expected), 1)
            precision = (len(expected & retrieved) / max(len(retrieved), 1)) if retrieved else 0.0
            grounded = _heuristic_grounded(answer, [c.title for c in chunks])

        results.append(EvalResult(
            question=item["question"],
            category=item["category"],
            expected_source_ids=item["expected_source_ids"],
            retrieved_source_ids=retrieved_source_ids,
            answer=answer,
            recall_at_k=recall,
            precision_source=precision,
            grounded=grounded,
        ))
    return results


def summarize(results: list[EvalResult]) -> dict[str, float]:
    n = len(results)
    if n == 0:
        return {"mean_recall_at_k": 0.0, "mean_precision_source": 0.0, "groundedness_rate": 0.0}
    return {
        "mean_recall_at_k": sum(r.recall_at_k for r in results) / n,
        "mean_precision_source": sum(r.precision_source for r in results) / n,
        "groundedness_rate": sum(1 for r in results if r.grounded) / n,
    }


def results_to_dicts(results: list[EvalResult]) -> list[dict[str, Any]]:
    return [asdict(r) for r in results]
