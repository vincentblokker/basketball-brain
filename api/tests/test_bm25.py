from app.retrieval.bm25_index import BM25Index
from app.schemas import Chunk


def make_chunk(idx: int, text: str) -> Chunk:
    return Chunk(
        chunk_id=f"c{idx}",
        source_id="src1",
        content_type="rule",
        audience=["coach"],
        age_category="all",
        language="nl",
        url="https://example.com",
        title="Test",
        chunk_index=idx,
        text=text,
    )


def test_bm25_query_returns_keyword_match_first():
    chunks = [
        make_chunk(0, "Wooden's Pyramid emphasises industriousness."),
        make_chunk(1, "De 24-secondenklok in basketbal wordt gereset."),
        make_chunk(2, "FIBA regels voor scheidsrechters."),
    ]
    bm25 = BM25Index(chunks)
    results = bm25.query("24 secondenklok", top_k=3)
    assert results[0] == "c1"  # keyword match should rank first


def test_bm25_handles_empty_corpus():
    # Should not crash with no chunks
    bm25 = BM25Index([])
    results = bm25.query("anything", top_k=3)
    assert results == []
