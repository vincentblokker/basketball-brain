import tempfile

import pytest

from app.retrieval.chroma_store import ChromaStore
from app.schemas import Chunk


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as tmp:
        yield ChromaStore(persist_dir=tmp, collection_name="test")


def make_chunk(idx: int, text: str, content_type: str = "rule") -> Chunk:
    return Chunk(
        chunk_id=f"c{idx}",
        source_id="src1",
        content_type=content_type,  # type: ignore[arg-type]
        audience=["coach"],
        age_category="all",
        language="nl",
        url="https://example.com",
        title="Test",
        chunk_index=idx,
        text=text,
    )


def test_add_and_count(store):
    chunks = [
        make_chunk(0, "De 24-secondenklok wordt gereset bij offensive rebound."),
        make_chunk(1, "Wooden's Pyramid emphasises industriousness."),
    ]
    store.add(chunks)
    assert store.count() == 2


def test_query_returns_relevant_chunk(store):
    chunks = [
        make_chunk(0, "De 24-secondenklok in basketbal is gereset bij offensive rebound."),
        make_chunk(1, "Wooden's Pyramid of Success has 15 building blocks."),
    ]
    store.add(chunks)
    results = store.query("hoe lang is shot clock?", top_k=1)
    assert len(results) == 1
    assert "secondenklok" in results[0].text or "24" in results[0].text


def test_all_chunks_returns_inserted(store):
    chunks = [make_chunk(i, f"chunk text {i}") for i in range(5)]
    store.add(chunks)
    fetched = store.all_chunks()
    assert len(fetched) == 5
    fetched_ids = {c.chunk_id for c in fetched}
    assert fetched_ids == {f"c{i}" for i in range(5)}


def test_tenant_isolation(store):
    a = make_chunk(0, "team A content")
    b = make_chunk(1, "team B content")
    b.tenant_id = "other"
    store.add([a, b])
    public_chunks = store.query("content", top_k=10, tenant_id="public")
    other_chunks = store.query("content", top_k=10, tenant_id="other")
    assert len(public_chunks) == 1
    assert public_chunks[0].chunk_id == "c0"
    assert len(other_chunks) == 1
    assert other_chunks[0].chunk_id == "c1"


def test_empty_add_is_noop(store):
    store.add([])
    assert store.count() == 0
