import tempfile
from unittest.mock import MagicMock

from app.eval.runner import evaluate, summarize
from app.eval.testset import TESTSET
from app.retrieval.bm25_index import BM25Index
from app.retrieval.chroma_store import ChromaStore
from app.schemas import Chunk


def make_chunk(source_id: str, idx: int, text: str) -> Chunk:
    return Chunk(
        chunk_id=f"{source_id}-c{idx}",
        source_id=source_id,
        content_type="rule",
        audience=["coach"],
        age_category="all",
        language="nl",
        url=f"https://example.com/{source_id}",
        title=f"{source_id.upper()} Document",
        chunk_index=idx,
        text=text,
    )


def test_evaluate_returns_one_result_per_question():
    with tempfile.TemporaryDirectory() as tmp:
        # Seed with chunks matching some expected source ids
        store = ChromaStore(persist_dir=tmp, collection_name="eval_test")
        store.add([
            make_chunk("nbb-spelregels-2025-2026", 0, "De shot clock is 24 seconden in NBB."),
            make_chunk("fiba-rules-2024", 0, "FIBA shot clock is 24 seconds. 14s reset."),
            make_chunk("wooden-pyramid", 0, "Industriousness is the foundation."),
        ])
        bm25 = BM25Index(store.all_chunks())

        # Mock LLM — returns canned text varying by content
        gen = MagicMock()
        def fake_answer(question, chunks):
            if "out-of-scope" in str(chunks) or len(chunks) == 0:
                return "Ik weet het niet op basis van de beschikbare bronnen."
            # For lookup-style, mention 'NBB Document' so the heuristic groundedness fires
            if "shot clock" in question.lower() or "secondenklok" in question.lower():
                return "De shot clock is 24 seconden volgens NBB-SPELREGELS-2025-2026 Document."
            return "Algemeen antwoord met verwijzing naar Document."
        gen.answer.side_effect = fake_answer

        results = evaluate(store, bm25, gen, top_k=5)
        assert len(results) == len(TESTSET)
        # Each result has the right shape
        for r in results:
            assert r.question
            assert r.category in {"lookup", "philosophy", "multi-doc", "out-of-scope"}
            assert 0.0 <= r.recall_at_k <= 1.0
            assert 0.0 <= r.precision_source <= 1.0


def test_summarize_computes_means():
    from app.eval.runner import EvalResult
    results = [
        EvalResult(
            question="q1", category="lookup",
            expected_source_ids=["a"], retrieved_source_ids=["a"],
            answer="x", recall_at_k=1.0, precision_source=1.0, grounded=True,
        ),
        EvalResult(
            question="q2", category="lookup",
            expected_source_ids=["b"], retrieved_source_ids=["c"],
            answer="x", recall_at_k=0.0, precision_source=0.0, grounded=False,
        ),
    ]
    summary = summarize(results)
    assert summary["mean_recall_at_k"] == 0.5
    assert summary["mean_precision_source"] == 0.5
    assert summary["groundedness_rate"] == 0.5


def test_summarize_handles_empty():
    assert summarize([]) == {
        "mean_recall_at_k": 0.0,
        "mean_precision_source": 0.0,
        "groundedness_rate": 0.0,
    }


def test_out_of_scope_idk_counted_correct():
    """Out-of-scope question with 'Ik weet het niet' answer should score recall=1."""
    from app.eval.runner import evaluate
    with tempfile.TemporaryDirectory() as tmp:
        store = ChromaStore(persist_dir=tmp, collection_name="oos_test")
        store.add([make_chunk("nbb-spelregels-2025-2026", 0, "Iets over basketbal.")])
        bm25 = BM25Index(store.all_chunks())
        gen = MagicMock()
        gen.answer.return_value = "Ik weet het niet op basis van de beschikbare bronnen."
        results = evaluate(store, bm25, gen, top_k=5)
        oos_results = [r for r in results if r.category == "out-of-scope"]
        assert all(r.recall_at_k == 1.0 for r in oos_results)
        assert all(r.grounded for r in oos_results)
