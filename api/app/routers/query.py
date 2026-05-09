import time

from fastapi import APIRouter, Depends

from app.config import settings
from app.deps import get_bm25, get_generator, get_metrics, get_store
from app.generation.llm import LLMGenerator
from app.metrics.store import MetricsStore
from app.retrieval.bm25_index import BM25Index
from app.retrieval.chroma_store import ChromaStore
from app.retrieval.hybrid import hybrid_retrieve_with_metrics
from app.schemas import Citation, QueryRequest, QueryResponse

router = APIRouter()

_StoreDep = Depends(get_store)
_BM25Dep = Depends(get_bm25)
_GenDep = Depends(get_generator)
_MetricsDep = Depends(get_metrics)


_OOS_MARKERS = ("weet het niet", "i don't know", "ik weet")


def _is_oos(answer: str) -> bool:
    lo = answer.lower()
    return any(m in lo for m in _OOS_MARKERS)


@router.post("/query", response_model=QueryResponse)
def query(
    req: QueryRequest,
    store: ChromaStore = _StoreDep,
    bm25: BM25Index = _BM25Dep,
    gen: LLMGenerator = _GenDep,
    metrics: MetricsStore = _MetricsDep,
) -> QueryResponse:
    t0 = time.perf_counter()
    error: str | None = None
    answer = ""
    chunks = []
    retrieval_metrics: dict[str, float] = {}
    try:
        chunks, retrieval_metrics = hybrid_retrieve_with_metrics(
            req.question, store, bm25,
            top_k=req.top_k, tenant_id=req.tenant_id, filters=req.filters,
        )
        answer = gen.answer(req.question, chunks)
    except Exception as e:
        error = str(e)
        raise
    finally:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        try:
            metrics.log_query(
                question=req.question,
                tenant_id=req.tenant_id,
                top_k=req.top_k,
                retrieved_count=len(chunks),
                citation_source_ids=list({c.source_id for c in chunks}),
                answer_length=len(answer),
                is_oos=_is_oos(answer),
                mean_similarity=retrieval_metrics.get("mean_vector_similarity"),
                latency_ms=latency_ms,
                llm_model=settings.llm_model,
                error=error,
            )
        except Exception:
            # Metrics logging must never break the user-facing path.
            pass

    citations = [
        Citation(
            source_id=c.source_id,
            title=c.title,
            url=c.url,
            section=c.section,
            page=c.page,
            chunk_id=c.chunk_id,
        )
        for c in chunks
    ]
    return QueryResponse(answer=answer, citations=citations, retrieved_chunks=chunks)
