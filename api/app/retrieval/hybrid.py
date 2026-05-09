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
    """Hybrid retrieval: vector + BM25 + RRF fusion. Returns chunks only."""
    chunks, _ = hybrid_retrieve_with_metrics(
        question, store, bm25,
        top_k=top_k, tenant_id=tenant_id, filters=filters,
        candidate_pool=candidate_pool,
        vector_weight=vector_weight, keyword_weight=keyword_weight,
    )
    return chunks


def hybrid_retrieve_with_metrics(
    question: str,
    store: ChromaStore,
    bm25: BM25Index,
    top_k: int = 5,
    tenant_id: str = "public",
    filters: dict[str, str] | None = None,
    candidate_pool: int = 50,
    vector_weight: float = 1.0,
    keyword_weight: float = 1.0,
) -> tuple[list[Chunk], dict[str, float]]:
    """Hybrid retrieval that also returns per-call metrics.

    Metrics dict contains:
    - mean_vector_similarity: float ∈ [0, 1] across the vector-lane top-N.
      Computed as 1 - mean(cosine_distance).

    1. Vector lane retrieves `candidate_pool` chunks (with distances).
    2. BM25 lane retrieves `candidate_pool` ids via lexical scoring.
    3. RRF fuses both rankings.
    4. Returns top_k Chunk objects + metrics.
    """
    vector_chunks, vector_distances = store.query_with_distances(
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
    chunks = [by_id[i] for i in fused_ids if i in by_id]

    if vector_distances:
        # Cap at top_k for similarity proxy — that's what the user effectively saw.
        top_distances = vector_distances[:top_k]
        mean_sim = max(0.0, 1.0 - sum(top_distances) / len(top_distances))
    else:
        mean_sim = 0.0
    metrics = {"mean_vector_similarity": mean_sim}

    return chunks, metrics


def _passes_filters(
    chunk: Chunk, tenant_id: str, filters: dict[str, str] | None
) -> bool:
    if chunk.tenant_id != tenant_id:
        return False
    if not filters:
        return True
    return all(getattr(chunk, key, None) == value for key, value in filters.items())
