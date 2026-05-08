"""One-shot ingest of MVP corpus. Run from repo root with venv active.

Pre-requisites:
- Run `scripts/download_sources.sh` first (or manually populate `api/data/raw/`)
- Activate venv: `source api/.venv/bin/activate`
"""
import sys
from pathlib import Path

# Add api/ to sys.path so `app` imports work when run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

from app.config import settings
from app.ingest.pipeline import ingest_corpus
from app.retrieval.chroma_store import ChromaStore


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    raw_dir = repo_root / "api" / "data" / "raw"
    manifest = raw_dir / "sources.json"
    chroma_dir = repo_root / "api" / settings.chroma_persist_dir.lstrip("./")
    store = ChromaStore(persist_dir=str(chroma_dir))
    total = ingest_corpus(raw_dir, manifest, store)
    print(f"\nDone. Total chunks: {total}")


if __name__ == "__main__":
    main()
