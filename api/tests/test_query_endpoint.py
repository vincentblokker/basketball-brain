import tempfile
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.deps import get_generator, get_store
from app.main import app
from app.retrieval.chroma_store import ChromaStore
from app.schemas import Chunk


def make_chunk(idx: int, text: str) -> Chunk:
    return Chunk(
        chunk_id=f"c{idx}",
        source_id="src1",
        content_type="rule",
        audience=["coach"],
        age_category="all",
        language="nl",
        url="https://example.com/source",
        title="Test Source",
        section=f"sec-{idx}",
        chunk_index=idx,
        text=text,
    )


@pytest.fixture
def client_with_mocks(monkeypatch):
    """Build a TestClient where get_store and get_generator are dependency-overridden."""
    with tempfile.TemporaryDirectory() as tmp:
        # Real Chroma store with seeded data — exercises full retrieval path
        store = ChromaStore(persist_dir=tmp, collection_name="test_query")
        store.add([
            make_chunk(0, "De 24-secondenklok wordt gereset bij offensive rebound."),
            make_chunk(1, "Een time-out duurt 60 seconden volgens de NBB."),
            make_chunk(2, "Wooden's Pyramid emphasises industriousness as a foundation."),
        ])

        # Mock LLM — no real network call
        mock_gen = MagicMock()
        mock_gen.answer.return_value = "De shot clock is 24 seconden. Bronnen: Test Source — sec-0"

        app.dependency_overrides[get_store] = lambda: store
        app.dependency_overrides[get_generator] = lambda: mock_gen

        try:
            yield TestClient(app), mock_gen, store
        finally:
            app.dependency_overrides.clear()


def test_query_returns_answer_with_citations(client_with_mocks):
    client, mock_gen, _store = client_with_mocks
    response = client.post(
        "/query",
        json={"question": "Hoe lang is de shot clock?", "top_k": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert "shot clock" in data["answer"].lower()
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["title"] == "Test Source"
    assert data["citations"][0]["url"] == "https://example.com/source"
    # LLM was called once with the question
    mock_gen.answer.assert_called_once()
    args, _kwargs = mock_gen.answer.call_args
    assert args[0] == "Hoe lang is de shot clock?"
    # Retrieved chunks were passed
    assert len(args[1]) >= 1


def test_query_default_top_k(client_with_mocks):
    client, _mock_gen, _store = client_with_mocks
    response = client.post("/query", json={"question": "test"})
    assert response.status_code == 200


def test_query_with_tenant_filter_returns_empty_for_unknown_tenant(client_with_mocks):
    client, _mock_gen, _store = client_with_mocks
    response = client.post(
        "/query",
        json={"question": "shot clock", "tenant_id": "nonexistent_tenant"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["retrieved_chunks"] == []
