import json
import tempfile
from pathlib import Path

from app.ingest.pipeline import ingest_corpus
from app.retrieval.chroma_store import ChromaStore


def test_ingest_corpus_with_synthetic_source():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        # Synthetic source: a small txt file
        source_text = "Basketbal kent een 24-secondenklok. " * 50
        (raw_dir / "synthetic.txt").write_text(source_text)

        manifest = [{
            "id": "synthetic",
            "file": "synthetic.txt",
            "title": "Synthetic Test Source",
            "content_type": "rule",
            "audience": ["coach"],
            "age_category": "all",
            "language": "nl",
            "url": "https://example.com",
            "source_type": "primary",
        }]
        manifest_path = raw_dir / "sources.json"
        manifest_path.write_text(json.dumps(manifest))

        store = ChromaStore(persist_dir=str(tmp_path / "chroma"), collection_name="ingest_test")
        total = ingest_corpus(raw_dir, manifest_path, store, chunk_size=200, overlap=40)

        assert total > 0
        assert store.count() == total

        results = store.query("shot clock", top_k=1)
        assert len(results) == 1
        assert results[0].source_id == "synthetic"


def test_ingest_corpus_skips_missing_files():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        manifest = [{
            "id": "nonexistent",
            "file": "missing.pdf",
            "title": "Missing",
            "content_type": "general",
            "audience": ["all"],
            "age_category": "all",
            "language": "nl",
            "url": "n/a",
            "source_type": "primary",
        }]
        manifest_path = raw_dir / "sources.json"
        manifest_path.write_text(json.dumps(manifest))
        store = ChromaStore(persist_dir=str(tmp_path / "chroma"), collection_name="missing_test")
        total = ingest_corpus(raw_dir, manifest_path, store)
        assert total == 0
