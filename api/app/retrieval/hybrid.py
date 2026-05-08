from app.retrieval.bm25_index import BM25Index
from app.retrieval.chroma_store import ChromaStore
from app.schemas import Chunk


def rrf_fusion(
    rank_lists: list[list[str]],
    weights: list[float] | None = None,
    k: int = 60,
) -> list[str]:
    """Reciprocal Rank Fusion. Combines multiple ranked id-lists into one.
    Higher-ranked items in any list contribute more. Documents present in
    multiple lists accumulate score.

    Args:
        rank_lists: list of ranked id-lists (e.g. [vector_ids, keyword_ids])
        weights: optional per-list multiplier. Default: equal weight 1.0 each.
        k: RRF constant (default 60, from original RRF paper).

    Returns:
        List of ids ordered by descending fused score.
    """
    if weights is None:
        weights = [1.0] * len(rank_lists)
    scores: dict[str, float] = {}
    for ranking, weight in zip(rank_lists, weights, strict=False):
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + weight / (k + rank + 1)
    return [
        doc_id
        for doc_id, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    ]


def hybrid_retrieve(
    question: str,
    store: ChromaStore,
    bm25: BM25Index,
    top_k: int = 5,
    tenant_id: str = "public",
    filters: dict[str, str] | None = None,
    candidate_pool: int = 50,
    vector_weight: float = 1.0,
    keyword_weight: float = 1.0,
) -> list[Chunk]:
    """Hybrid retrieval: vector + BM25 + RRF fusion.

    1. Vector lane retrieves `candidate_pool` chunks via ChromaStore.
    2. BM25 lane retrieves `candidate_pool` ids via lexical scoring.
    3. RRF fuses both rankings.
    4. Returns top_k Chunk objects.
    """
    vector_chunks = store.query(
        question, top_k=candidate_pool, tenant_id=tenant_id, filters=filters
    )
    vector_ids = [c.chunk_id for c in vector_chunks]

    # BM25 lane retrieves over the entire indexed corpus; apply the same
    # tenant + metadata filters so tenant isolation is preserved across lanes.
    raw_keyword_ids = bm25.query(question, top_k=candidate_pool)
    bm25_by_id: dict[str, Chunk] = {c.chunk_id: c for c in bm25.chunks}
    keyword_ids = [
        cid
        for cid in raw_keyword_ids
        if cid in bm25_by_id and _passes_filters(bm25_by_id[cid], tenant_id, filters)
    ]

    fused_ids = rrf_fusion(
        [vector_ids, keyword_ids],
        weights=[vector_weight, keyword_weight],
    )[:top_k]

    by_id: dict[str, Chunk] = {c.chunk_id: c for c in vector_chunks}
    for cid in keyword_ids:
        by_id.setdefault(cid, bm25_by_id[cid])
    return [by_id[i] for i in fused_ids if i in by_id]


def _passes_filters(
    chunk: Chunk, tenant_id: str, filters: dict[str, str] | None
) -> bool:
    if chunk.tenant_id != tenant_id:
        return False
    if not filters:
        return True
    return all(getattr(chunk, key, None) == value for key, value in filters.items())
