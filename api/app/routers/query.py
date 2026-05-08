from fastapi import APIRouter, Depends

from app.deps import get_bm25, get_generator, get_store
from app.generation.llm import LLMGenerator
from app.retrieval.bm25_index import BM25Index
from app.retrieval.chroma_store import ChromaStore
from app.retrieval.hybrid import hybrid_retrieve
from app.schemas import Citation, QueryRequest, QueryResponse

router = APIRouter()

_StoreDep = Depends(get_store)
_BM25Dep = Depends(get_bm25)
_GenDep = Depends(get_generator)


@router.post("/query", response_model=QueryResponse)
def query(
    req: QueryRequest,
    store: ChromaStore = _StoreDep,
    bm25: BM25Index = _BM25Dep,
    gen: LLMGenerator = _GenDep,
) -> QueryResponse:
    chunks = hybrid_retrieve(
        req.question,
        store,
        bm25,
        top_k=req.top_k,
        tenant_id=req.tenant_id,
        filters=req.filters,
    )
    answer = gen.answer(req.question, chunks)
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
